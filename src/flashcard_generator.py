def create_flashcards(questions):
    if not isinstance(questions, list):
        return {"error": "Input must be a list of questions"}
    
    if not questions:
        return {"error": "Input list cannot be empty"}
    
    flashcards = []
    for i, q in enumerate(questions):
        card = {
            "id": i,
            "question": q.get("question", "No question generated"),
            "answer": q.get("answer", "No answer generated"),
        }
        flashcards.append(card)
    return flashcards
