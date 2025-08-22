# from langchain_community.llms.ollama import Ollama
from langchain_ollama import OllamaLLM
from config.settings import Config
from langchain_core.prompts import ChatPromptTemplate
import re

class QueryEngine:
    def __init__(self, vectordb_manager, llm_model: str = Config.LLM_MODEL):
        self.vectordb = vectordb_manager
        self.llm_model = llm_model
    
    def query(self, question: str, n_results: int = 5):
        """Query the vector database and generate LLM response"""
        print(f"🔍 Searching for: {question}")
        
        # Vector search
        try:
            results = self.vectordb.similarity_search_with_score(
                query=question,
                k=n_results,
                # filter={'source': "tweet"}
            )
                        
            if not results:
                print("❌ No relevant documents found.")
                return None
            
            results = sorted(results, key=lambda x: x[1], reverse=True)
            
            # Prepare context
            context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
            context_text_output = "\n\n---\n\n".join([f"Context #{i+1}\n\n{doc.page_content}" for i, (doc, _score) in enumerate(results)]) 
            person_type = "child"

            # Generate LLM response
            PROMPT_TEMPLATE = '''
            You are a knowledgeable and concise museum tour guide.
            Use the context below to answer the question directly.
            Do not mention or cite any materials, contexts, texts or documents were referred to.

            ---

            Context:
            {context}

            Question: {question}

            Format your answer like this:

            Thought:
            ...

            Answer:
            ...

            '''

            prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
            prompt = prompt_template.format(context=context_text, question=question, person_type=person_type)
            
            print("\n🤖 Generating response...")
            # response = ollama.generate(model=self.llm_model, prompt=prompt)
            model = OllamaLLM(model=self.llm_model)
            response_text = model.invoke(prompt)
            # Extract <think>...</think> block (optional)
            # think_match = re.search(r"<think>(.*?)</think>", response_text, re.DOTALL)
            # chain_of_thought = think_match.group(1).strip() if think_match else None

            # Handle deepseek-r1's specific output format
            # First, remove any <think>...</think> blocks
            response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL)
            
            # Try multiple patterns to handle different output formats
            # Pattern 1: **Thought:** and **Answer:** (markdown format)
            thought_pattern_md = r'\*\*Thought:\*\*\s*(.*?)(?=\*\*Answer:\*\*|$)'
            answer_pattern_md = r'\*\*Answer:\*\*\s*(.*?)(?=\*\*\w+:\*\*|$)'
            
            # Pattern 2: Thought: and Answer: (plain format)
            thought_pattern_plain = r'(?:^|\n)Thought:\s*(.*?)(?=\nAnswer:|$)'
            answer_pattern_plain = r'(?:^|\n)Answer:\s*(.*?)(?=\n\w+:|$)'
            
            # Try markdown format first
            thought_match = re.search(thought_pattern_md, response_text, re.DOTALL | re.IGNORECASE)
            answer_match = re.search(answer_pattern_md, response_text, re.DOTALL | re.IGNORECASE)
            
            # If markdown format doesn't work, try plain format
            if not thought_match or not answer_match:
                thought_match = re.search(thought_pattern_plain, response_text, re.DOTALL | re.IGNORECASE)
                answer_match = re.search(answer_pattern_plain, response_text, re.DOTALL | re.IGNORECASE)
            
            thought = thought_match.group(1).strip() if thought_match else "No thought provided"
            answer = answer_match.group(1).strip() if answer_match else "No answer provided"

            # Extract sources (you already have them from n_results)
            source_list = [res.metadata['doc_tag'] for res, _score in results]  
            
            results_dict = {'c': context_text_output,
                            't': thought,
                            'a': answer,
                            's': source_list,
                            }
            return results_dict
        # print(f"{context_text_output}\n\n---\n\n💭 THOUGHT: {thought}\n\n🖋️ ANSWER: {answer}\n\nℹ️ SOURCES: {source_list}")
            
        except Exception as e:
            print(f"❌ Error during query: {e}")
            return None

