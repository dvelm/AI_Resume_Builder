from typing import Dict, Type
from selenium.webdriver.remote.webdriver import WebDriver

from src.job_boards.job_board_interface import JobBoardInterface
from src.job_boards.indeed import Indeed
from src.job_boards.ziprecruiter import ZipRecruiter


class JobBoardFactory:
    """Factory for creating job board instances"""
    
    # Registry of available job boards
    _registry: Dict[str, Type[JobBoardInterface]] = {
        "indeed": Indeed,
        "ziprecruiter": ZipRecruiter,
    }
    
    @classmethod
    def create(cls, board_name: str, driver: WebDriver) -> JobBoardInterface:
        """Create a job board instance by name"""
        board_class = cls._registry.get(board_name.lower())
        if not board_class:
            raise ValueError(f"Unsupported job board: {board_name}")
        
        return board_class(driver)
    
    @classmethod
    def get_supported_boards(cls) -> list:
        """Get list of supported job boards"""
        return list(cls._registry.keys())
