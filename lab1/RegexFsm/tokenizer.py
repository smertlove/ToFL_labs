from enum import Enum
from typing import Callable


class State(Enum):
    START        = 000
    REPITITION   = 1
    OR           = 2
    CHAR         = 3
    ESCAPE       = 4
    END_B        = 5
    END          = 777
    ERR          = 666


class Token(Enum):
    REPETITION = 1
    OR         = 2
    SLASH      = 3
    CHAR       = 4
    OPEN_B     = 5
    CLOSE_B    = 6
    END        = 777


def extend_(l: list[list[str]], ch: str) -> list[list[str]]:
    l[-1] = l[-1] + ch
    return l


def append_(l: list[list[str]], ch: str) -> list[list[str]]:
    l.append(ch)
    return l


def pass_(l: list[list[str]], ch: str) -> list[list[str]]:
    return l


class TemplateError(Exception):
    def __init__(self, template, i):            
        err_pos = i * " " + " ^"
        message = (
            f"{self.__class__.__name__}: Кривой шаблон в позиции {i}\n"
            + f"'{template}'"
            + "\n"
            + err_pos
        )

        super().__init__(message)


class Tokenizer:

    char_to_tok = {
        "*"  : Token.REPETITION,
        "+"  : Token.REPETITION,
        "?"  : Token.REPETITION,
        "|"  : Token.OR        ,
        "/"  : Token.SLASH     ,
        "END": Token.END       ,
    }

    @classmethod
    def get_tok_by_char(cls, char: str) -> Token:
        """
            Получить имя токена по символу (одному, либо Token.END по "END")
        """
        return cls.char_to_tok.get(
            char,
            Token.CHAR
        )

    validation_grammar: dict[
        State,
        dict[
            Token,
            tuple[
                State,
                Callable[
                    [
                        list[
                            list[str]
                        ],
                        str    
                    ],
                    None
                ]
            ]
        ]
    ] = {
        State.START: {
            Token.CHAR : (
                State.CHAR,
                append_
            ),
            Token.SLASH: (
                State.ESCAPE,
                pass_
            ),
            Token.END  : (
                State.END,
                pass_
            ),
            Token.OR        : (
                State.OR,
                append_
            ),
        },
        State.CHAR: {
            Token.CHAR      : (
                State.CHAR,
                append_
            ),
            Token.SLASH     : (
                State.ESCAPE,
                pass_
            ),
            Token.REPETITION: (
                State.REPITITION,
                extend_
            ),
            Token.OR        : (
                State.OR,
                append_
            ),
            Token.END       : (
                State.END,
                pass_
            ),
        },
        State.ESCAPE: {
            Token.REPETITION: (
                State.CHAR,
                append_
            ),
            Token.OR        : (
                State.CHAR,
                append_
            ),
            Token.SLASH     : (
                State.CHAR,
                append_
            ),
            Token.CHAR      : (
                State.CHAR,
                append_
            ),
        },
        State.REPITITION: {
            Token.OR   : (
                State.OR,
                append_
            ),
            Token.SLASH: (
                State.ESCAPE,
                pass_
            ),
            Token.CHAR : (
                State.CHAR,
                append_
            ),
            Token.END  : (
                State.END,
                pass_
            ),
        },
        State.OR: {
            Token.SLASH: (
                State.ESCAPE,
                pass_
            ),
            Token.CHAR : (
                State.CHAR,
                append_
            ),
            Token.OR : (
                State.OR,
                append_
            ),
            Token.END  : (
                State.END,
                pass_
            ),
        },
        State.ERR: dict(),
        State.END: dict(),
    }

    @classmethod
    def change_state(cls, cur_state: State, char: str) -> tuple[
        State, Callable[
            [
                list[str],
                str    
            ],
            None
        ]
    ]:
        """
            Получить новое состояние по текущему состоянию и одному входному символу (либо по "END").
        """
        tok = cls.get_tok_by_char(char)
        return cls.validation_grammar.get(
            cur_state,
            cls.validation_grammar[State.ERR]
        ).get(
            tok,
            (
                State.ERR,
                pass_
            ) 
        )

    @classmethod
    def tokenize(cls, regex_tmpl: str) -> list[list[str]]:
        tokens: list[str] = []

        cur_state = State.START

        for i, char in enumerate(regex_tmpl):
            cur_state, action = cls.change_state(cur_state, char)

            if cur_state == State.ERR:
                raise TemplateError(regex_tmpl, i)
            
            else:
                tokens = action(tokens, char)

        cur_state, action = cls.change_state(cur_state, "END")

        if cur_state == State.END:
            return tokens
        else:
            raise TemplateError(regex_tmpl, i)
