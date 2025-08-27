# from langchain_community.llms.ollama import Ollama
from langchain_ollama import OllamaLLM
from config.settings import Config
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
import re
import json

class QueryEngine:
    def __init__(self, vectordb_manager, llm_model: str = Config.LLM_MODEL, multiq_model: str = Config.MULTIQ_MODEL):
        self.vectordb = vectordb_manager
        self.llm_model = llm_model
        self.multiq_model = multiq_model
    
    def query(self, question: str, n_results: int = 5):
        """Query the vector database and generate LLM response"""
        print(f"🔍 Searching for: {question}")
                           
        # Vector search
        
            # results = self.vectordb.similarity_search_with_score(
            #     query=question,
            #     k=n_results,
            #     # filter={'source': "tweet"}
            # )
                        
            # if not results:
            #     print("❌ No relevant documents found.")
            #     return None
            
            # results = sorted(results, key=lambda x: x[1], reverse=True)

        # Multiquery handling
        system = """You have the ability to issue search queries to get information to help answer user questions.

        Analyze the question and decide:
        - If the question requires multiple distinct pieces of information, generate multiple search queries
        - If the question is simple and can be answered with a single search, use just one query
        - If the original question is already well-formed for search, you can use it as-is

        Return your response as JSON in this format: {{"searches": [{{"query": "search term 1"}}, {{"query": "search term 2"}}]}}
        For single queries, just return: {{"searches": [{{"query": "the original or modified query"}}]}}"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system),
            ("human", "{question}"),  # Only {question} variable
        ])

        query_model = OllamaLLM(model=self.multiq_model, format="json", temperature=0)

        def parse_searches(response):
            try:
                data = json.loads(response)
                return data.get("searches", [])
            except:
                return [{"query": response.strip()}]

        query_analyzer = (
            {"question": RunnablePassthrough()}  # Only pass question
            | prompt 
            | query_model 
            | parse_searches
        )

        # # Test
        # question = "what are the differences in diet between sauropods and crocodiles?"
        search_queries = query_analyzer.invoke(question)
        print("Generated searches:", search_queries)

        # Prepare context
        results = []
        seen_doc_ids = set()
        
        for search_item in search_queries:
            search_query = search_item.get('query', question)
            
            try:
                search_results = self.vectordb.similarity_search_with_score(
                    query=search_query,
                    k=n_results
                )
                
                for search_result, score in search_results:
                    # Avoid duplicates by checking doc_tag
                    doc_id = search_result.id
                    if doc_id and doc_id not in seen_doc_ids:
                        results.append((search_result, score))
                        seen_doc_ids.add(doc_id)

                results = sorted(results, key=lambda x: x[1], reverse=True)

            except Exception as e:
                print(f"⚠️ Search failed for '{search_query}': {e}")
                continue
            

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


