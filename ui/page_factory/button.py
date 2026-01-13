from ui.page_factory.component import Component


class Button(Component):
    @property
    def type_of(self) -> str:
        return "button"

    async def hover(self, **kwargs) -> None:
        with self._action_step("hover"):
            locator = self.get_locator(**kwargs)
            await locator.hover()

    async def double_click(self, **kwargs) -> None:
        with self._action_step("double click"):
            locator = self.get_locator(**kwargs)
            await locator.dblclick()
