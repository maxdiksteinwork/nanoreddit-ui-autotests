from pydantic import BaseModel

from utils.data_generators.fake_credentials import faker


class PublishPostDTO(BaseModel):
    title: str
    content: str

    @classmethod
    def random(cls) -> "PublishPostDTO":
        return cls(
            title=faker.sentence(nb_words=5),
            content=faker.paragraph(nb_sentences=2),
        )


class AddCommentDTO(BaseModel):
    text: str

    @classmethod
    def random(cls) -> "AddCommentDTO":
        return cls(text=faker.sentence(nb_words=5))


class ReplyCommentDTO(BaseModel):
    text: str

    @classmethod
    def random(cls) -> "ReplyCommentDTO":
        return cls(text=faker.sentence(nb_words=6))
