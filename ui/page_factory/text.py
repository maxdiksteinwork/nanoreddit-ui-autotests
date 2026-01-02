from playwright.async_api import expect

from ui.page_factory.component import Component


class Text(Component):
    @property
    def type_of(self) -> str:
        return "text"

    async def should_contain_text(self, text: str, **kwargs) -> None:
        with self._action_step(f'assert text contains "{text}"'):
            locator = self.get_locator(**kwargs)
            await expect(locator).to_contain_text(text)

    async def should_not_contain_text(self, text: str, **kwargs) -> None:
        with self._action_step(f'assert text does not contain "{text}"'):
            locator = self.get_locator(**kwargs)
            await expect(locator).not_to_contain_text(text)
