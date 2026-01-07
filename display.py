"""
LCD display helper — show 'Benign' or 'Malignant' on a character LCD.

Tries to use `RPLCD.i2c.CharLCD` (common on Raspberry Pi with an I2C PCF8574 backpack).
If the library or hardware isn't available it falls back to printing the result.

Usage:
	from display import show_result_on_lcd
	show_result_on_lcd('benign')
"""

from typing import Literal

ResultType = Literal['benign', 'malignant']


def _format_text(result: ResultType) -> str:
	label = 'Benign' if result.lower() == 'benign' else 'Malignant'
	# For a 16x2 LCD keep it short and on two lines
	return f"Result:\n{label}"


def show_result_on_lcd(result: ResultType, i2c_addr: int = 0x27) -> None:
	"""Display the result on an attached character LCD or print if unavailable.

	- `result` must be 'benign' or 'malignant' (case-insensitive).
	- `i2c_addr` is the I2C address of the PCF8574 backpack (commonly 0x27 or 0x3f).
	"""
	text = _format_text(result)

	try:
		# Prefer RPLCD (works with many Pi + I2C backpacks)
		from RPLCD.i2c import CharLCD

		lcd = CharLCD('PCF8574', i2c_addr, cols=16, rows=2)
		lcd.clear()
		lcd.write_string(text)
		return
	except Exception:
		# If RPLCD not available or hardware error, fall through to print
		pass

	try:
		# Try Adafruit_CharLCD as an alternative (GPIO-driven LCD)
		# This block is intentionally minimal; adapt pin numbers if you use this backend.
		from Adafruit_CharLCD import Adafruit_CharLCD

		# Example pin wiring (modify as needed): rs, en, d4, d5, d6, d7
		lcd = Adafruit_CharLCD(25, 24, 23, 17, 18, 22, cols=16, lines=2)
		lcd.clear()
		for i, line in enumerate(text.split('\n')):
			lcd.set_cursor(0, i)
			lcd.message(line)
		return
	except Exception:
		pass

	# Final fallback: print to console
	print('LCD not available —', text.replace('\n', ' | '))


if __name__ == '__main__':
	# Quick demo when run directly
	show_result_on_lcd('benign')

