from rag import answer_question

question = "Cos'è l'intelligenza artificiale?"
answer, sources = answer_question(question)

print("DOMANDA:", question)
print("\nRISPOSTA:", answer)
print("\nFONTI:", sources)