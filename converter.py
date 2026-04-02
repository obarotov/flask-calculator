from collections import Counter


class UnitConverter:
    def __init__(self):
        self.data = {
            "length": {
                "base": "meters",
                "factors": {
                    "millimeters": 0.001,
                    "centimeters": 0.01,
                    "meters": 1.0,
                    "kilometers": 1000.0,
                    "inches": 0.0254,
                    "feet": 0.3048,
                    "miles": 1609.34
                }
            },
            "weight": {
                "base": "grams",
                "factors": {
                    "milligrams": 0.001,
                    "grams": 1.0,
                    "kilograms": 1000.0,
                    "ounces": 28.3495,
                    "pounds": 453.592
                }
            },
            "temperature": {
                "base": "celsius",
                "factors": None
            }
        }

    def convert(self, category, value, from_unit, to_unit):
        from_unit = from_unit.lower()
        to_unit = to_unit.lower()
        if category not in self.data:
            raise ValueError(f"Unsupported category: {category}")

        if category == "temperature":
            return self._convert_temperature(value, from_unit, to_unit)

        factors = self.data[category]["factors"]
        if from_unit not in factors or to_unit not in factors:
            raise ValueError(f"Invalid units for {category}.")

        base_value = value * factors[from_unit]
        result = base_value / factors[to_unit]
        return round(result, 4)

    def _convert_temperature(self, value, from_unit, to_unit):
        conversion = self._get_temperature_conversion(from_unit, to_unit)
        if conversion is None:
            raise ValueError(f"Unsupported temperature conversion: {from_unit} to {to_unit}")
        return round(conversion(value), 4)

    def _get_temperature_conversion(self, from_unit, to_unit):
        conversions = {
            ("celsius", "celsius"):       lambda x: x,
            ("celsius", "fahrenheit"):    lambda x: (x * 9/5) + 32,
            ("celsius", "kelvin"):        lambda x: x + 273.15,
            ("fahrenheit", "celsius"):    lambda x: (x - 32) * 5/9,
            ("fahrenheit", "fahrenheit"): lambda x: x,
            ("fahrenheit", "kelvin"):     lambda x: (x - 32) * 5/9 + 273.15,
            ("kelvin", "celsius"):        lambda x: x - 273.15,
            ("kelvin", "fahrenheit"):     lambda x: (x - 273.15) * 9/5 + 32,
            ("kelvin", "kelvin"):         lambda x: x
        }
        return conversions.get((from_unit, to_unit))

    def get_units(self, category):
        if category not in self.data:
            raise ValueError(f"Category '{category}' not found.")
        if category == "temperature":
            return ["celsius", "fahrenheit", "kelvin"]
        return list(self.data[category]["factors"].keys())