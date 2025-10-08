import logging
from PIL import Image, ImageDraw
from typing import Tuple

from seedsigner.gui.components import GUIConstants, Fonts
from seedsigner.gui.screens.screen import BaseScreen, RET_CODE__BACK_BUTTON
from seedsigner.hardware.buttons import HardwareButtonsConstants

logger = logging.getLogger(__name__)


class ColorPickerScreen(BaseScreen):
    """
    256-color palette picker screen
    Displays a grid of colors for user selection
    """

    def __init__(self, current_color: str = "#000000", title: str = "Select Logo Color"):
        super().__init__()
        self.title = title
        self.current_color = current_color

        # Grid configuration (16x16 = 256 colors)
        self.grid_cols = 16
        self.grid_rows = 16
        self.cell_size = 12
        self.grid_padding = 2

        # Calculate grid position (centered)
        grid_width = self.grid_cols * self.cell_size
        grid_height = self.grid_rows * self.cell_size
        self.grid_x = int((self.canvas_width - grid_width) / 2)
        self.grid_y = 50  # Leave space for title

        # Selection cursor
        self.selected_row = 0
        self.selected_col = 0

        # Try to find current color in palette
        try:
            current_r, current_g, current_b = self._hex_to_rgb(current_color)
            for row in range(self.grid_rows):
                for col in range(self.grid_cols):
                    r, g, b = self._get_color_at_position(row, col)
                    if abs(r - current_r) < 20 and abs(g - current_g) < 20 and abs(b - current_b) < 20:
                        self.selected_row = row
                        self.selected_col = col
                        break
        except:
            pass


    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


    def _get_color_at_position(self, row: int, col: int) -> Tuple[int, int, int]:
        """
        Get RGB color for a grid position
        Creates a 256-color palette (16x16 grid)
        """
        index = row * self.grid_cols + col

        # Generate a 256-color palette
        # Using 6x6x6 RGB cube + 16 grayscale colors
        if index < 216:  # 6x6x6 = 216 colors
            r = (index // 36) * 51
            g = ((index % 36) // 6) * 51
            b = (index % 6) * 51
        else:  # Grayscale ramp
            gray_index = index - 216
            gray = int(gray_index * 255 / 39)
            r = g = b = gray

        return (r, g, b)


    def _get_selected_color_hex(self) -> str:
        """Get the currently selected color as hex string"""
        r, g, b = self._get_color_at_position(self.selected_row, self.selected_col)
        return f"#{r:02x}{g:02x}{b:02x}"


    def _render(self):
        self.clear_screen()

        # Draw title
        title_font = Fonts.get_font(GUIConstants.get_top_nav_title_font_name(),
                                     GUIConstants.get_top_nav_title_font_size())
        title_width = self.renderer.draw.textlength(self.title, font=title_font)
        title_x = int((self.canvas_width - title_width) / 2)
        self.renderer.draw.text((title_x, 10), self.title,
                                fill=GUIConstants.ACCENT_COLOR, font=title_font)

        # Draw color grid
        for row in range(self.grid_rows):
            for col in range(self.grid_cols):
                x = self.grid_x + col * self.cell_size
                y = self.grid_y + row * self.cell_size

                r, g, b = self._get_color_at_position(row, col)
                color = (r, g, b)

                # Draw color cell
                self.renderer.draw.rectangle(
                    [(x, y), (x + self.cell_size - 1, y + self.cell_size - 1)],
                    fill=color
                )

                # Draw selection highlight
                if row == self.selected_row and col == self.selected_col:
                    # Draw white border for selection
                    self.renderer.draw.rectangle(
                        [(x, y), (x + self.cell_size - 1, y + self.cell_size - 1)],
                        outline="white",
                        width=2
                    )

        # Show selected color info
        selected_hex = self._get_selected_color_hex()
        info_font = Fonts.get_font(GUIConstants.get_body_font_name(),
                                    GUIConstants.get_body_font_size())
        info_text = f"Selected: {selected_hex}"
        info_y = self.grid_y + self.grid_rows * self.cell_size + 15
        self.renderer.draw.text((self.grid_x, info_y), info_text,
                                fill="white", font=info_font)

        # Instructions
        instructions = "Arrow keys: Move | SELECT: Confirm | BACK: Cancel"
        inst_font = Fonts.get_font(GUIConstants.get_body_font_name(),
                                    GUIConstants.get_body_font_size() - 2)
        inst_y = self.canvas_height - 20
        self.renderer.draw.text((5, inst_y), instructions,
                                fill="#888", font=inst_font)


    def _run(self):
        """Handle user input for color selection"""
        while True:
            # Render current state
            with self.renderer.lock:
                self._render()
                self.renderer.show_image()

            # Wait for input
            input = self.hw_inputs.wait_for([
                HardwareButtonsConstants.KEY_UP,
                HardwareButtonsConstants.KEY_DOWN,
                HardwareButtonsConstants.KEY_LEFT,
                HardwareButtonsConstants.KEY_RIGHT,
                HardwareButtonsConstants.KEY_PRESS,
                HardwareButtonsConstants.KEY1,
                HardwareButtonsConstants.KEY2,
                HardwareButtonsConstants.KEY3,
            ])

            # Navigation
            if input == HardwareButtonsConstants.KEY_UP:
                self.selected_row = max(0, self.selected_row - 1)
            elif input == HardwareButtonsConstants.KEY_DOWN:
                self.selected_row = min(self.grid_rows - 1, self.selected_row + 1)
            elif input == HardwareButtonsConstants.KEY_LEFT:
                self.selected_col = max(0, self.selected_col - 1)
            elif input == HardwareButtonsConstants.KEY_RIGHT:
                self.selected_col = min(self.grid_cols - 1, self.selected_col + 1)

            # Confirm selection
            elif input == HardwareButtonsConstants.KEY_PRESS:
                return self._get_selected_color_hex()

            # Cancel (back button)
            elif input in [HardwareButtonsConstants.KEY1, HardwareButtonsConstants.KEY2,
                          HardwareButtonsConstants.KEY3]:
                return RET_CODE__BACK_BUTTON
