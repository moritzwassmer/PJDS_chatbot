#Typing
from typing import Callable

class ChatbotInterface:
    def __init__(self, solrhandler: Callable, clusterer: Callable, topicdeterminator: Callable, initial_query: str, maxResultSetSize: int) -> None:
        pass
    def generateQuestion(self) -> str:
        pass
    def refineResultset(self, userResponse: bool) -> None:
        pass
    def isFinished(self) -> bool:
        pass
    def get_result_string(self) -> str:
        pass
    def get_result_html(self) -> str:
        pass
    def add_query(self, query: str) -> None:
        pass