DDL_GRAMMAR = """
start: instruction+

instruction: (ddl_create | ddl_use | ddl_alter | ddl_drop | dml_insert) ";"

ddl_use: "USE"i VAR

ddl_create: "CREATE"i (DATABASE [ddl_exists] VAR
                     | TABLE [ddl_exists] VAR ddl_table_struct)

ddl_exists: "IF"i [/NOT/i] "EXISTS"i

ddl_table_struct: "(" ddl_var_def ("," ddl_var_def)* ("," set_key)*")"
ddl_var_def: VAR DATATYPE optional_attr*
// ddl_var_def: VAR DATATYPE ( key? dafault? not_null?
//                         | key? not_null? dafault?
//                         | not_null? dafault? key?
//                         | not_null? key? dafault?
//                         | dafault? not_null? key?
//                         | dafault? key? not_null?)

optional_attr: default | not_null | key

default: "DEFAULT"i (DATAVAL | "CURRENT_TIMESTAMP"i)
not_null: "NOT"i "NULL"i

key: (primary_key | foreign_key)
foreign_key: "FOREIGN"i "KEY"i "REFERENCES"i VAR "(" VAR ")" on_option*
on_option: "ON"i (/DELETE/i
                | /UPDATE/i) (/RESTRICT/i
                            | /CASCADE/i
                            | /SET/i /NULL/i
                            | /SET/i /DEFAULT/i
                            | /NO/i /ACTION/i)
primary_key: "PRIMARY"i "KEY"i [/AUTOINCREMENT/i]

set_key: set_foreign | set_primary
set_foreign: "FOREIGN"i "KEY"i "(" VAR ")" "REFERENCES"i VAR "(" VAR ")"
set_primary: "PRIMARY"i "KEY"i "(" VAR ")"

ddl_alter: "ALTER"i "TABLE"i ddl_exists? VAR (ddl_alter_add | ddl_alter_drop | ddl_alter_alter)
ddl_alter_add: "ADD"i ddl_var_def
ddl_alter_drop: "DROP"i "COLUMN"i VAR
ddl_alter_alter: "ALTER"i "COLUMN"i VAR DATATYPE? optional_attr*

ddl_drop:  "DROP"i  [TABLE | DATABASE] ddl_exists VAR

keys_tuple: "(" VAR ["," VAR]* ")"
values_tuple: "(" DATAVAL ["," DATAVAL]* ")"
dml_insert: "INSERT"i "INTO"i VAR keys_tuple? "VALUES"i values_tuple ["," values_tuple]*

TABLE: "TABLE"i
DATABASE: "DATABASE"i

VAR: /[a-zA-Z_][a-zA-Z0-9_]*/

STR: /"[^"]*"/ | /'[^']*'/

OPT_SIGN: /-/?
NUMBER: /[0-9]/+
INT: OPT_SIGN NUMBER
FLOAT: OPT_SIGN NUMBER /./ NUMBER

NULL: /NULL/ | /(N|n)ull/
BOOL: /(T|t)rue/|/(F|f)alse/

DATETIME: DATE " " TIME
DATE: YEAR "-" MONTH "-" DAY
TIME: HOUR ":" MINUTE ":" SECOND ["." MILLISECOND]

YEAR: /[0-9]{4}/
MONTH: /[0-9]{2}/
DAY: /[0-9]{2}/
HOUR: /[0-9]{2}/
MINUTE: /[0-9]{2}/
SECOND: /[0-9]{2}/
MILLISECOND: /[0-9]{3}/

DATATYPE: "INT"i
        |"FLOAT"i
        |"BOOLEAN"i
        |"CHAR"i["(" NUMBER ")"]
        |"varCHAR"i["(" NUMBER ")"]
        |"TEXT"i["(" NUMBER ")"]
        |"DATETIME"i
        |"DATE"i
        |"TIME"i
        |"YEAR"i
        |"MONTH"i
        |"DAY"i
        |"HOUR"i
        |"MINUTE"i
        |"SECOND"i
        |"MILLISECOND"i

DATAVAL: STR
        |FLOAT
        |INT
        |NULL
        |BOOL
        |DATETIME
        |DATE
        |TIME
        |YEAR
        |MONTH
        |DAY
        |HOUR
        |MINUTE
        |SECOND
        |MILLISECOND

%import common.NEWLINE
%import common.WS_INLINE
%ignore WS_INLINE
%ignore NEWLINE
"""
