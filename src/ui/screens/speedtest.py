"""
Speed test screen placeholder.
"""
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen


class SpeedTestScreen(Screen):
    """Speed test screen (placeholder)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self) -> None:
        """Build the UI."""
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        with layout.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)
        layout.bind(size=self._update_rect, pos=self._update_rect)

        # Back button
        btn_back = Button(
            text='← Back to Menu',
            size_hint=(1, 0.1),
            background_color=(0.3, 0.3, 0.3, 1)
        )
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'menu'))
        layout.add_widget(btn_back)

        # Title
        title = Label(
            text='[b]Speed Test[/b]\n\n(Coming Soon)',
            markup=True,
            font_size='32sp',
            color=(0.2, 0.8, 1, 1)
        )
        layout.add_widget(title)

        self.add_widget(layout)

    def _update_rect(self, instance, value) -> None:
        self.rect.pos = instance.pos
        self.rect.size = instance.size
