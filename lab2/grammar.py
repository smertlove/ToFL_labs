from lark import Lark


ddl_grammar = """

start: instruction+

instruction: (ddl_create_table | ddl_alter_table | ddl_drop_table) ";"

ddl_create_table: "CREATE" "TABLE" VAR ddl_if_not_exists ddl_table_struct
ddl_if_not_exists: ["IF" "NOT" "EXISTS"]
ddl_table_struct: "(" ddl_var_def ["," ddl_var_def]* ")"
ddl_var_def: VAR DATATYPE [key] [["NOT"] NULL]
key: (primary_key | foreign_key)
foreign_key: "FOREIGN" "KEY" "REFERENCES" VAR "(" VAR ")"
primary_key: "PRIMARY" " "+ "KEY" [ " "+ "AUTOINCREMENT"]

ddl_alter_table: "ALTER" "TABLE" VAR (ddl_alter_add | ddl_alter_drop | ddl_alter_alter)
ddl_alter_add: "ADD" ddl_var_def
ddl_alter_drop: "DROP" "COLUMN" VAR
ddl_alter_alter: "ALTER" "COLUMN" ddl_var_def

ddl_drop_table:  "DROP" "TABLE" VAR

VAR: ("a".."z")+

NUMBER: ("0".."9")+
NULL: "NULL"
DATATYPE: ("INT"|"FLOAT"|"CHAR"["(" NUMBER ")"])

%import common.NEWLINE
%import common.WS_INLINE
%ignore WS_INLINE
%ignore NEWLINE

"""
import re


ddl_code = """

CREATE TABLE user IF NOT EXISTS (
    id INT PRIMARY KEY AUTOINCREMENT NOT NULL,
    name CHAR,
    age INT,
    type INT FOREIGN KEY REFERENCES types(id)
);

ALTER TABLE user ADD surname CHAR(222);
ALTER TABLE user DROP COLUMN  surname;
ALTER TABLE user ALTER COLUMN name CHAR(345) NOT NULL;

DROP TABLE user;

"""



dml_grammar = """



"""

