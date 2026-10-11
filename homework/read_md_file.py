from pathlib import Path
import json
from typing import Literal

from gitsource.chunking import chunk_documents
from minsearch import Index
from openai import OpenAI
from pydantic import BaseModel, Field


BOOKS_DIR = Path(__file__).with_name("books_text")
openai_client = OpenAI()


class RAGResponse(BaseModel):
    answer: str = Field(description="The main answer to the user's question in markdown")
    found_answer: bool = Field(description="True if relevant information was found in the documentation")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    confidence_explanation: str = Field(description="Explanation about the confidence level")
    answer_type: Literal[
        "how-to",
        "explanation",
        "troubleshooting",
        "comparison",
        "reference",
    ] = Field(description="The category of the answer")
    followup_questions: list[str] = Field(description="Suggested follow-up questions")


instructions = """
You're a course assistant, your task is to answer the QUESTION from the
course students using the provided CONTEXT
"""

prompt_template = """
<QUESTION>
{question}
</QUESTION>

<CONTEXT>
{context}
</CONTEXT>
""".strip()

books = []

for file_path in sorted(BOOKS_DIR.glob("*.md")):
    text = file_path.read_text(encoding="utf-8")
    non_empty_lines = [line for line in text.splitlines() if line.strip()]
    books.append({
        "source": file_path.name,
        "content": non_empty_lines,
    })

chunks = chunk_documents(books, size=100, step=50)
documents = [
    {**chunk, "content": "\n".join(chunk["content"])}
    for chunk in chunks
]

index = Index(text_fields=["content"])
index.fit(documents)


def build_prompt(question, search_results):
    context = json.dumps(search_results, indent=2)
    return prompt_template.format(
        question=question,
        context=context,
    ).strip()


def search(question):
    return index.search(question, num_results=5)


def llm(user_prompt, instructions, model="gpt-4o-mini"):
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_prompt},
    ]
    response = openai_client.responses.parse(
        model=model,
        input=messages,
        text_format=RAGResponse,
    )
    if response.usage is None:
        raise RuntimeError("The OpenAI response did not include token usage.")
    if response.output_parsed is None:
        raise RuntimeError("The OpenAI response did not contain a parsed RAG response.")

    return (
        response.output_parsed,
        response.usage.input_tokens,
        response.usage.output_tokens,
    )


def rag(query):
    search_results = search(query)
    prompt = build_prompt(query, search_results)
    return llm(prompt, instructions)


if __name__ == "__main__":
    query = "python function definition"
    rag_response, input_tokens, output_tokens = rag(query)
    print(f"Answer: {rag_response.answer}")
    print(f"Found answer: {rag_response.found_answer}")
    print(f"Confidence: {rag_response.confidence}")
    print(f"Confidence explanation: {rag_response.confidence_explanation}")
    print(f"Answer type: {rag_response.answer_type}")
    print(f"Follow-up questions: {rag_response.followup_questions}")
    print(f"Input tokens: {input_tokens}")
    print(f"Output tokens: {output_tokens}")
    print(f"More input tokens than Q5: {input_tokens - 7929}")
    print(f"Indexed {len(documents)} chunks from {len(books)} books")