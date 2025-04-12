from typing import Optional
from pydantic import BaseModel


class Pagination(BaseModel):
    current_page: int
    total_pages: int
    total_records: int
    record_per_page: int
    previous_page_url: Optional[str]
    next_page_url: Optional[str]