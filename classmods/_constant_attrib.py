class ConstantAttrib:
    """
    Descriptor that acts as a constant attribute.
    It allows setting the value once (either at initialization or first assignment),
    and prevents any further changes.
    """

    def __init__(self, name = None):
        self.name = name

    def __set_name__(self, owner, name):
        # Called when the descriptor is assigned to a class attribute
        if self.name is None:
            self.name = name
        self.private_name = f"_{name}_constant_value"

    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.private_name not in instance.__dict__:
            raise AttributeError(f"Constant attribute '{self.name}' has not been set yet.")
        return instance.__dict__[self.private_name]

    def __set__(self, instance, value):
        if self.private_name in instance.__dict__:
            raise AttributeError(f"Cannot modify constant attribute '{self.name}' once it is set.")
        instance.__dict__[self.private_name] = value

    def __delete__(self, instance):
        raise AttributeError(f"Cannot delete constant attribute '{self.name}'.")
