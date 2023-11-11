import functools

import pytest
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel, Field

import instructor
from instructor.patch import is_async, wrap_chatcompletion

client = instructor.patch(OpenAI())


def test_runmodel():
    class UserExtract(BaseModel):
        name: str
        age: int

    model = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=UserExtract,
        messages=[
            {"role": "user", "content": "Extract jason is 25 years old"},
        ],
    )
    assert isinstance(model, UserExtract), "Should be instance of UserExtract"
    assert model.name.lower() == "jason"
    assert hasattr(
        model, "_raw_response"
    ), "The raw response should be available from OpenAI"


def test_runmodel_validator():
    from pydantic import field_validator

    class UserExtract(BaseModel):
        name: str
        age: int

        @field_validator("name")
        @classmethod
        def validate_name(cls, v):
            if v.upper() != v:
                raise ValueError("Name should be uppercase")
            return v

    model = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=UserExtract,
        max_retries=2,
        messages=[
            {"role": "user", "content": "Extract jason is 25 years old"},
        ],
    )
    assert isinstance(model, UserExtract), "Should be instance of UserExtract"
    assert model.name == "JASON"
    assert hasattr(
        model, "_raw_response"
    ), "The raw response should be available from OpenAI"


def test_patch_completes_successfully():
    instructor.patch(OpenAI())


def test_apatch_completes_successfully():
    instructor.apatch(AsyncOpenAI())


@pytest.mark.asyncio
async def test_wrap_chatcompletion_wraps_async_input_function():
    async def input_function(*args, **kwargs):
        return "Hello, World!"

    wrapped_function = wrap_chatcompletion(input_function)
    result = await wrapped_function()

    assert result == "Hello, World!"


def test_wrap_chatcompletion_wraps_input_function():
    def input_function(*args, **kwargs):
        return "Hello, World!"

    wrapped_function = wrap_chatcompletion(input_function)
    result = wrapped_function()

    assert result == "Hello, World!"


def test_is_async_returns_true_if_function_is_async():
    async def async_function():
        pass

    assert is_async(async_function) is True


def test_is_async_returns_false_if_function_is_not_async():
    def sync_function():
        pass

    assert is_async(sync_function) is False


def test_is_async_returns_true_if_wrapped_function_is_async():
    async def async_function():
        pass

    @functools.wraps(async_function)
    def wrapped_function():
        pass

    assert is_async(wrapped_function) is True
