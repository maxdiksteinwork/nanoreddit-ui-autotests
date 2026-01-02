from playwright.async_api import expect

from ui.page_factory.component import Component


class Textarea(Component):
    @property
    def type_of(self) -> str:
        return "textarea"

    async def fill(self, value: str, *, validate_value: bool = False, **kwargs) -> None:
        with self._action_step(f'fill with "{value}"'):
            locator = self.get_locator(**kwargs)
            await locator.fill(value)
            if validate_value:
                await self.should_have_value(value, **kwargs)

    async def should_have_value(self, value: str, **kwargs) -> None:
        with self._action_step(f'assert value is "{value}"'):
            locator = self.get_locator(**kwargs)
            await expect(locator).to_have_value(value)
