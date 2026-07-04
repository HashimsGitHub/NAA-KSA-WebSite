from dataclasses import dataclass


@dataclass
class BlogPost:
    post_id: str
    title: str
    slug: str
    summary: str
    author_email: str
    author_name: str
    markdown_blob_path: str = ""
    cover_image_url: str = ""
    tags: str = ""
    status: str = "draft"
    views: int = 0
    likes: int = 0
    created_at: str = ""
    submitted_at: str = ""
    approved_by: str = ""
    approved_at: str = ""
    published_at: str = ""
    updated_at: str = ""
