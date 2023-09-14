from collections import deque
import openai
import tiktoken
from mem import LongTermMemory


class LLMAgent:
    def __init__(self, api_key, max_context_len=4097):
        """
        Initialize the OpenAI API with the provided key.
        """
        openai.api_key = api_key
        self.messages = deque()
        self.objective = None
        self.max_context_len = max_context_len

    def num_tokens_from_messages(self, model="gpt-3.5-turbo-0613"):
        """
        Return the number of tokens used by a list of messages.
        src: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        """
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            print("Warning: model not found. Using cl100k_base encoding.")
            encoding = tiktoken.get_encoding("cl100k_base")
        if model in {
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-16k-0613",
            "gpt-4-0314",
            "gpt-4-32k-0314",
            "gpt-4-0613",
            "gpt-4-32k-0613",
            }:
            tokens_per_message = 3
            tokens_per_name = 1
        elif model == "gpt-3.5-turbo-0301":
            tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif "gpt-3.5-turbo" in model:
            print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
            return self.num_tokens_from_messages(model="gpt-3.5-turbo-0613")
        elif "gpt-4" in model:
            print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
            return self.num_tokens_from_messages(model="gpt-4-0613")
        else:
            raise NotImplementedError(
                f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
            )
        num_tokens = 0
        for message in self.messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(encoding.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

    def create_agent(self, objective):
        """
        Given a high-level objective, create a fresh LLM instance to generate an appropriate role for the agent.
        """
        self.messages.append({"role": "user", "content": f"Briefly define a role for an agent to accomplish the objective: {objective}. Do not repeat any information provided in the objective."})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=list(self.messages)
        )
        role = response.choices[0].message['content']
        print(f'Created new agent with objective: {objective}.\n Role: {role}')
        self.messages.append({"role": "assistant", "content": role})
        while self.num_tokens_from_messages() > self.max_context_len:
            self.messages.popleft()
        return role

    def prompt_agent(self, prompt):
        """
        Given a prompt, format it correctly and ask the agent to generate a response.
        """
        # Remind the model of its role and the overarching objective
        self.messages.append({"role": "system", "content": f"You are an agent with the role: {self.messages[-1]['content']}. Your overarching objective is: {self.objective}"})
        self.messages.append({"role": "user", "content": prompt})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=list(self.messages)
        )
        agent_response = response.choices[0].message['content']
        self.messages.append({"role": "assistant", "content": agent_response})
        return agent_response

# Example usage:
# agent = AutonomousAgent("YOUR_OPENAI_API_KEY")
# agent.create_agent("Write a Python class")
# response = agent.prompt_agent("How do I start?")
# print(response)
