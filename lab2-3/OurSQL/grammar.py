DDL_GRAMMAR = """
start: instruction+

?instruction: (ddl_create | ddl_show | ddl_use | ddl_alter | ddl_drop) ";"

ddl_use: "USE"i VAR

ddl_show: "SHOW"i (/DATABASES/i | /TABLES/i)

ddl_create: "CREATE"i (DATABASE [ddl_exists] VAR
                     | TABLE [ddl_exists] VAR ddl_table_struct)
ddl_exists: "IF"i [/NOT/i] "EXISTS"i
ddl_table_struct: "(" ddl_var_def ("," ddl_var_def)* ("," set_key)*")"

ddl_var_def: VAR DATATYPE optional_attr*
?optional_attr: default | not_null | key
default: "DEFAULT"i (dataval | /CURRENT_TIMESTAMP/i)
not_null: "NOT"i "NULL"i

?key: primary_key | foreign_key
foreign_key: "FOREIGN"i "KEY"i "REFERENCES"i VAR "(" VAR ")" [on_option]*
on_option: "ON"i (/DELETE/i | /UPDATE/i) (/RESTRICT/i
                            | /CASCADE/i
                            | /SET/i /NULL/i
                            | /SET/i /DEFAULT/i
                            | /NO/i /ACTION/i)
primary_key: "PRIMARY"i "KEY"i [/AUTOINCREMENT/i]

?set_key: set_foreign | set_primary
set_foreign: "FOREIGN"i "KEY"i "(" VAR ")" "REFERENCES"i VAR "(" VAR ")" [on_option]*
set_primary: "PRIMARY"i "KEY"i "(" VAR ")"

ddl_alter: "ALTER"i "TABLE"i ddl_exists? VAR (ddl_alter_add | ddl_alter_drop | ddl_alter_alter)
ddl_alter_add: "ADD"i ddl_var_def
ddl_alter_drop: "DROP"i "COLUMN"i VAR
ddl_alter_alter: "ALTER"i "COLUMN"i VAR [DATATYPE] optional_attr*

ddl_drop:  "DROP"i  [TABLE | DATABASE] [ddl_exists] VAR

TABLE: "TABLE"i
DATABASE: "DATABASE"i
VAR: /[a-zA-Z_][a-zA-Z0-9_]*/
str: /"[^"]*"/ | /'[^']*'/

NUMBER: /[0-9]/+
int: /-/? NUMBER
float: /-/? NUMBER /./ NUMBER
null: /NULL/ | /(N|n)ull/
bool: /(T|t)rue/|/(F|f)alse/

DATATYPE: "INT"i
        |"FLOAT"i
        |"BOOLEAN"i
        |"STR"i

?dataval: str
        |float
        |int
        |null
%import common.NEWLINE
%import common.WS_INLINE
%ignore WS_INLINE
%ignore NEWLINE
"""
