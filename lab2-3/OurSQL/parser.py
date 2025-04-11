from lark import Lark, Transformer
from .grammar import DDL_GRAMMAR


class Beautifier(Transformer):

    def ddl_exists(self, items):
        return items[0] is None


class PrimaryKey:

    def __init__(self):
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}"


class ForeignKey:

    def __init__(self, table, column, update="restrict", delete="restrict"):
        self.table = table
        self.column = column
        self.update = update
        self.delete = delete

    def __repr__(self):
        return f"{self.__class__.__name__} references {self.table}({self.column}), on update: {self.update}, on delete: {self.delete}"


class Field:

    def __init__(self, name, dtype="str", default=None, null=True, key=None):
        self.name = name
        self.dtype   = dtype
        self.default = default 
        self.null=null
        self.key=key

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, type={self.dtype}, default={self.default}, nullable={self.null}{", " + repr(self.key) if self.key is not None else ""})"


class OurSQLInterpreter:

    parser = Lark(DDL_GRAMMAR, start='start', parser="earley")

    pipe = (
        # DuplicateAttributeChecker(),
        Beautifier(),
    )

    def __init__(self):
        self.databases = {"__MAIN__": dict()}
        self.cursor = "__MAIN__"

    def __repr__(self):
        return f"{self.__class__.__name__}(selected:{self.cursor}, databases:{self.databases})"

    def select(self, database:str):
        if database not in self.databases:
            raise ValueError(f"Database \"{database}\" does not exist.")
        self.cursor = database

    def _parse_string(self, string:str):
        tree = self.parser.parse(string)
        for transformer in self.pipe:
            tree = transformer.transform(tree)
        return tree

    def run(self, string:str):
        tree = self._parse_string(string)

        for instruction in tree.children:
            if instruction.data.value == "ddl_create":
                self.create(*instruction.children)

            elif instruction.data.value == "ddl_use":
                self.use(*instruction.children)

            elif instruction.data.value == "ddl_show":
                self.show(*instruction.children)

            elif instruction.data.value == "ddl_drop":
                self.drop(*instruction.children)

    def drop(self, entity, exists, name):

        entity_str = entity.value.lower()
        name_str = name.value

        if exists is not  None and not exists:
            raise ValueError("Not exists in this context is always an error")
        
        if entity_str == "database":
            if name_str not in self.databases:
                if exists is None:
                    raise ValueError(f"Database {name_str} does not exist")
                else:
                    return
        
            del self.databases[name_str]
        
        elif entity_str == "table":
            if name_str not in self.databases[self.cursor]:
                if exists is None:
                    raise ValueError(f"Database {name_str} does not exist")
                else:
                    return
            del self.databases[self.cursor][name_str]
    
    def use(self, dbname):
        self.cursor = dbname.value

    def show(self, tok):
        val = tok.value.lower()

        if val == "databases":
            print("Existing databases:")
            for db in self.databases:
                ln = len(self.databases[db])
                print(db, f"{ln} table{("s","")[ln == 1]}{("", '\t'+"<--")[self.cursor == db]}")

        elif val == "tables":
            print(f"Tables of {self.cursor} database:")
            for table in self.databases[self.cursor]:
                print(table, self.databases[self.cursor][table])

    def create(self, entity, exists, name, struct=None):

        entity_str = entity.value.lower()

        if exists:
            raise ValueError("IF EXISTS всегда ведет к ошибке")

        name_str = name.value
        if entity_str == "database":

            if name_str in self.databases:
                if exists is None:
                    raise ValueError(f"Database \"{name_str}\" already exists.")
                else:
                    return
            
            self.databases[name_str] = dict()

        elif entity_str == "table":
            if name_str in self.databases[self.cursor]:
                if exists is None:
                    raise ValueError(f"Table \"{name_str}\" already exists in {self.cursor}.")
                else:
                    return
                
            self.databases[self.cursor][name_str] = self.create_table(struct)
            
        else:
            raise ValueError(f"Invalid entity \"{entity_str}\"")
        
    def create_key(self, tree):

        key_type = tree.data.value.lower()
        
        if key_type == "primary_key" or key_type == "set_primary":
            return PrimaryKey()
        elif key_type == "foreign_key" or  key_type == "set_foreign":
            if key_type == "set_foreign":
                args = tree.children[1:]
            else:
                args = tree.children
            kwargs = dict()

            for arg in args[2:]:
                option, action = map(lambda tok: tok.value.lower(), arg.children)
                if option in kwargs:
                    raise ValueError(f"Duplicate options {option}")
                else:
                    kwargs[option] = action

            return ForeignKey(args[0], args[1], **kwargs)
        else:
            raise ValueError(f"Unknown key type: \"{key_type}\"")

    def create_table(self, struct) -> dict:
        new_table = dict()

        for var_def in struct.children:
            var_def_name = var_def.data.value.lower()

            if var_def_name.split("_")[0] == "set":

                target_col = var_def.children[0].value
                if target_col not in new_table:
                    raise ValueError(f"Column {target_col} is not defined.")

                col = new_table[target_col]

                if col.key is not None:
                    raise ValueError(f"{target_col} is already a {col.key.__class__.__name__}.")

                
                new_table[target_col].key = self.create_key(var_def)

            else:
                schema = var_def.children

                name = schema[0]
                if name.value in new_table:
                    raise ValueError(f"Column {name} is already defined.")


                datatype = schema[1].lower()

                kwargs = {
                    "name": name,
                    "dtype": datatype,
                    "default": None,
                    "null": True,
                    "key": None
                }

                visited_attrs = set()
    
                for optional_attr in schema[2:]:

                    attr_name = optional_attr.data.lower()

                    if attr_name in visited_attrs:
                        raise ValueError(f"Дублирование атрибутов")
                    else:
                        visited_attrs.add(attr_name)

                    if attr_name == "foreign_key" or attr_name == "primary_key":
                        val = self.create_key(optional_attr)
                    elif attr_name == "default":
                        dtype = optional_attr.children[0].data.lower()
                        val = optional_attr.children[0].children[0].value
                        if dtype != kwargs['dtype']:
                            raise ValueError(f"Value {val} doesnt match type {kwargs['dtype']}")

                    else:
                        val = optional_attr.data.value

                    attr_name = attr_name.split("_")[1] if "_" in attr_name else attr_name
                    kwargs[attr_name] = val

                new_table[name.value] = (Field(**kwargs))

        return new_table
