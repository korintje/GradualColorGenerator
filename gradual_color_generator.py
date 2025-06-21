from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QColorDialog, QLabel, QSpinBox, QTextEdit, QFileDialog, QComboBox, QScrollArea
)
from PySide6.QtGui import QColor
import sys
from datetime import datetime
import math

def generate_colors(start_color, end_color, count, mode):
    colors = []
    r1, g1, b1 = start_color.red(), start_color.green(), start_color.blue()
    r2, g2, b2 = end_color.red(), end_color.green(), end_color.blue()

    for i in range(count):
        if count == 1:
            factor = 0
        else:
            linear_factor = i / (count - 1)
            if mode == "Linear":
                factor = linear_factor
            elif mode == "Square root":
                factor = math.sqrt(linear_factor)
            elif mode == "Square":
                factor = linear_factor ** 2
            else:
                factor = linear_factor

        new_r = int(r1 + (r2 - r1) * factor)
        new_g = int(g1 + (g2 - g1) * factor)
        new_b = int(b1 + (b2 - b1) * factor)
        colors.append(QColor(new_r, new_g, new_b))
    return colors

def colors_to_veusz(colors):
    lines = [
        "# Veusz custom definitions (version 3.2.1)",
        f"# Saved at {datetime.now().isoformat()}",
        ""
    ]
    for i, c in enumerate(colors, 1):
        lines.append(f"AddCustom(u'color', u'theme{i}', u'{c.name()}')")
    return "\n".join(lines)

class ColorGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Veusz Custom Color Generator")
        self.layout = QVBoxLayout()

        # START COLOR
        self.layout.addWidget(QLabel("Start Color:"))
        self.start_color_layout = self.create_color_input("#000000", self.on_field_change)
        self.layout.addLayout(self.start_color_layout)

        # END COLOR
        self.layout.addWidget(QLabel("End Color:"))
        self.end_color_layout = self.create_color_input("#ffffff", self.on_field_change)
        self.layout.addLayout(self.end_color_layout)

        # NUMBER OF COLORS
        self.layout.addWidget(QLabel("Number of colors:"))
        self.count_input = QSpinBox()
        self.count_input.setMinimum(1)
        self.count_input.setMaximum(100)
        self.count_input.setValue(5)
        self.count_input.valueChanged.connect(self.on_field_change)
        self.layout.addWidget(self.count_input)

        # GRADIENT MODE
        self.layout.addWidget(QLabel("Gradient mode:"))
        self.mode_select = QComboBox()
        self.mode_select.addItems(["Linear", "Square root", "Square"])
        self.mode_select.currentIndexChanged.connect(self.on_field_change)
        self.layout.addWidget(self.mode_select)

        # SAVE
        self.layout.addWidget(QLabel("Save the generated colors to a file:"))
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_to_file)
        self.layout.addWidget(self.save_button)

        # COLOR PREVIEW AREA
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.preview_container = QWidget()
        self.preview_layout = QHBoxLayout()
        self.preview_container.setLayout(self.preview_layout)
        self.scroll_area.setWidget(self.preview_container)
        self.layout.addWidget(self.scroll_area)

        # OUTPUT
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.layout.addWidget(self.output)

        # State
        self.start_color = QColor("#000000")
        self.end_color = QColor("#ffffff")
        self.colors = []
        self.veusz_text = ""

        self.setLayout(self.layout)

        # Initial generation
        self.generate_colors_and_update()

    def create_color_input(self, default_hex, text_changed_handler):
        layout = QHBoxLayout()

        swatch = QLabel()
        swatch.setFixedSize(24, 24)
        swatch.setStyleSheet(f"background-color: {default_hex}; border: 1px solid #000;")

        input_field = QLineEdit(default_hex)
        input_field.textChanged.connect(text_changed_handler)

        button = QPushButton("Pick Color")
        button.clicked.connect(lambda: self.pick_color(input_field))

        layout.addWidget(swatch)
        layout.addWidget(input_field)
        layout.addWidget(button)

        layout.swatch = swatch
        layout.input_field = input_field
        return layout

    def on_field_change(self):
        self.generate_colors_and_update()

    def update_swatch_and_color(self, layout, color):
        layout.swatch.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #000;")

    def pick_color(self, input_field):
        color = QColorDialog.getColor()
        if color.isValid():
            input_field.setText(color.name())

    def generate_colors_and_update(self):
        # Update colors from input
        start_hex = self.start_color_layout.input_field.text()
        end_hex = self.end_color_layout.input_field.text()

        start_color = QColor(start_hex)
        end_color = QColor(end_hex)

        if not (start_color.isValid() and end_color.isValid()):
            self.output.setPlainText("Invalid start or end color!")
            return

        self.start_color = start_color
        self.end_color = end_color
        self.update_swatch_and_color(self.start_color_layout, start_color)
        self.update_swatch_and_color(self.end_color_layout, end_color)

        count = self.count_input.value()
        mode = self.mode_select.currentText()

        self.colors = generate_colors(start_color, end_color, count, mode)
        self.veusz_text = colors_to_veusz(self.colors)
        self.output.setPlainText(self.veusz_text)
        self.update_color_previews(self.colors)

    def update_color_previews(self, colors):
        # Remove old previews
        while self.preview_layout.count():
            child = self.preview_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Add new previews
        for color in colors:
            swatch = QLabel()
            swatch.setFixedSize(24, 24)
            swatch.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #000;")
            self.preview_layout.addWidget(swatch)

    def save_to_file(self):
        if not self.veusz_text:
            self.output.setPlainText("No colors generated to save!")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Veusz Color File", "", "Veusz Color Scheme (*.vsz);;All Files (*)"
        )
        if filename:
            if not filename.endswith(".vsz"):
                filename += ".vsz"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.veusz_text)
            self.output.append(f"Saved to: {filename}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorGenerator()
    window.show()
    sys.exit(app.exec())
