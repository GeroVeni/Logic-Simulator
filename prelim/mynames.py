"""Implements a name table for lexical analysis.

Classes
-------
MyNames - implements a name table for lexical analysis.
"""


class MyNames:

	"""Implements a name table for lexical analysis.

	Parameters
	----------
	No parameters.

	Public methods
	-------------
	lookup(self, name_string): Returns the corresponding name ID for the
				 given name string. Adds the name if not already present.

	get_string(self, name_id): Returns the corresponding name string for the
				 given name ID. Returns None if the ID is not a valid index.
	"""

	def __init__(self):
		"""Initialise the names list."""
		self.namesList = []

	def lookup(self, name_string):
		"""Return the corresponding name ID for the given name_string.

		If the name string is not present in the names list, add it.
		"""
		for i in range(len(self.namesList)):
			if name_string == self.namesList[i]:
				return i

		# String was not found; add it
		self.namesList.append(name_string)
		return len(self.namesList) - 1

	def get_string(self, name_id):
		"""Return the corresponding name string for the given name_id.

		If the name ID is not a valid index into the names list, return None.
		"""
		if not isinstance(name_id, int):
			raise TypeError('name_id must be an int')
		if (name_id < 0):
			raise ValueError('name_id cannot be negative')
		
		if name_id < len(self.namesList):
			return self.namesList[name_id]

		return None

