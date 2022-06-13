class QuestionGenerator():

    def __init__(self) -> None:
        pass
    
    def generate_question(self, words) -> str:
        return "Geht es bei Ihrem Anliegen um {0} ?".format(" ".join(words))