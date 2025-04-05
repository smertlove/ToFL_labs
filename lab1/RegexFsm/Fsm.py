import uuid
from uuid import UUID

from typing import List, Type, Generic, TypeVar

from RegexFsm.tokenizer import Tokenizer


class FsmNode:

    def __init__(self, exitable=False) -> None:

        self.id = uuid.uuid4()

        ## {by: [to, ...]}
        self.transitions: dict[
            str,
            list["FsmNode"]
        ] = dict()

        self.exitable: bool = exitable

    def __repr__(self):
        return str(self.id)[:5]

    def get_data_for_repr(self):
        result = []

        for by_ in self.transitions:
            for node in self.transitions[by_]:
                result.append(
                    (
                        self.id,
                        node.id,
                        by_ if by_ is not None else "None",
                        ("", "*")[self.exitable]
                    )
                )

        if not result:
             result.append((self.id, "", "None", ("", "*")[self.exitable]))

        return result

    def __eq__(self, other: "FsmNode"):
        return self.id == other.id

    def target(self, other: "FsmNode", by_: str|None = None) -> tuple[int, int]:
        arr = self.transitions.get(by_, [])

        if other.id not in [node.id for node in arr]:
            self.transitions[by_] = arr + [other]

    def forget(self, by_, uuid_:UUID):

        self.transitions[by_].pop(
            next(
                filter(
                    lambda pair: pair[1].id == uuid_,
                    enumerate(self.transitions[by_])
                )
            )[0]
        )

    def del_e_edges(self):

        to_forget = []

        for targeted_node in self.transitions.get(None, []):

            to_forget.append(targeted_node.id)
            if targeted_node.exitable:
                self.exitable = True

            for by_ in targeted_node.transitions:
                for to_target_node in targeted_node.transitions[by_]:
                    self.target(to_target_node, by_)

        for forget in to_forget:
            self.forget(None, forget)

        if self.transitions.get(None, []):
            self.del_e_edges()

    def __hash__(self):
        return hash(self.id)


def zero_or_one(S: FsmNode, by_: str) -> None:
    """
        n?
    """

    Z  = FsmNode()
    S.target(Z, by_=None)

    if isinstance(by_, str):
        S.target(Z, by_=by_)

    else:
        fA = Fsm(by_)
        fa_ending_nodes = fA.get_ending_nodes()
        S.target(fA.head)

        for f_ending in fa_ending_nodes:
            f_ending.target(Z)
            f_ending.exitable = False

    return Z


def zero_or_more(S: FsmNode, by_: str) -> None:
    """
        n*
    """

    Z = FsmNode()
    if isinstance(by_, str):
        A = FsmNode()
        S.target(A, by_=None)
        A.target(Z, by_=None)
        A.target(A, by_=by_)

    else:
        fA = Fsm(by_)
        fa_ending_nodes = fA.get_ending_nodes()

        S.target(fA.head)
        S.target(Z)

        for f_ending in fa_ending_nodes:
            f_ending.target(fA.head)
            f_ending.target(Z)    
            f_ending.exitable = False

    return Z


def one_or_more(S: FsmNode, by_: str) -> None:
    """
        n+
    """

    Z = FsmNode()
    if isinstance(by_, str):
        A = FsmNode()

        S.target(A, by_=by_)
        A.target(Z, by_=None)
        A.target(A, by_=by_)

    else:
        fA1 = Fsm(by_)
        fa1_ending_nodes = fA1.get_ending_nodes()

        S.target(fA1.head)

        for f_ending in fa1_ending_nodes:
            f_ending.target(fA1.head)
            f_ending.target(Z)
            f_ending.exitable = False

    return Z


def one_ahead(S: FsmNode, by_: str|list) -> FsmNode:
    """
        nm
    """
    Z = FsmNode()
    if isinstance(by_, str):
        S.target(Z, by_=by_)

    else:
        f = Fsm(by_)
        f_ending_nodes = f.get_ending_nodes()
        S.target(f.head, None)
        for f_ending in f_ending_nodes:
            f_ending.target(Z)
            f_ending.exitable = False

    return Z

operator_to_func = {
    "*": zero_or_more,
    "+": one_or_more,
    "?": zero_or_one,
    None: one_ahead
}

def make_chain(tokens: list[str], operator_to_func=operator_to_func) -> FsmNode:

    head = FsmNode()
    tail = head
    for tok in tokens:

        ## tok может быть списком, тогда мы вынуждены костылять ##
        
        by_ = tok[0]

        if len(tok) == 2:
            operator = tok[1]
        else:
            operator = None

        tail = operator_to_func[operator](tail, by_)

    tail.exitable = True

    return head


def split_pattern(pattern: str):
    """
        "ab(cd(e)f(g))hij(kl)" -> ['ab', ['cd', ['e'], 'f', ['g']], 'hij', ['kl']]
    """

    result = [""]
    stack = [result]

    for char in pattern:
        curr_list = stack[-1] 

        if char == '(':
            new_list = [""]
            curr_list.append(new_list)
            stack.append(new_list)

        elif char == ")":
            stack.pop()

        else: 
            if isinstance(curr_list[-1], str):
                curr_list[-1] = curr_list[-1] + char
            else:
                curr_list.append(char)

    return result


class _Fsm:

    def __init__(self, pattern: str | list[str | list]):

        if isinstance(pattern, str):
            pieces = split_pattern(pattern)
        else:
            pieces = pattern

        self.head = FsmNode()

        alternatives = [[]]
        for i in range(len(pieces)):

            sub = pieces[i]

            if isinstance(sub, str):
                for token in Tokenizer.tokenize(sub):
                    if token == "|":
                        alternatives.append([])
                    else:
                        alternatives[-1].append(token)
            else:  # isinstance(sub, list):
                if (
                    i < len(pieces) - 1
                    and isinstance(pieces[i+1], str)
                    and pieces[i+1][0] in {"*", "+", "?"}
                ):
                    operator_or_None = pieces[i+1][0]
                    pieces[i+1] = pieces[i+1][1:]
                else:
                    operator_or_None = None

                alternatives[-1].append((sub, operator_or_None))

        for alternative in alternatives:
            self.head.target(make_chain(alternative), None)

        self.optimize()

    def get_ending_nodes(self):
        return [node for node in self.get_all_nodes() if node.exitable]

    def match(self, string):

        cur_node = self.head

        for char in string:
            if char in cur_node.transitions:
                cur_node = cur_node.transitions[char][0]
            else:
                return False
            
        return cur_node.exitable

    def get_all_nodes(self) -> list[FsmNode]:

        visited  : set[UUID]     = set()
        queue    : list[FsmNode] = [self.head]
        result   : list[FsmNode] = []

        while queue:
            current_node = queue.pop(0)

            if current_node.id not in visited:
                visited.add(current_node.id)
                result.append(current_node)

                for by_ in current_node.transitions:
                    for node in current_node.transitions[by_]:
                        if node.id not in visited:
                            queue.append(node)

        return result
    
    def __repr__(self):
        nodes = self.get_all_nodes()

        result = [
            f"{self.__class__.__name__}({len(nodes)} nodes)",
            "From\tTo\tBy\tExitable"
        ]

        names = {nodes[i].id: str(i) for i in range(len(nodes))}

        for node in nodes:
            data_for_repr = node.get_data_for_repr()

            for raw in data_for_repr:

                result.append(
                    "\t".join(
                        [
                            names[raw[0]],
                            names[raw[1]] if raw[1] else "",
                            raw[2],
                            raw[3]
                        ]
                    )
                )

        return "\n".join(result)
    
    def get_alphabet(self):
        alphabet = set()
        for node in self.get_all_nodes():
            for symbol in node.transitions.keys():
                if symbol is not None:
                    alphabet.add(symbol)
        return sorted(list(alphabet))


    def optimize(self):
        #  Удаление e-дуг
        nodes = self.get_all_nodes()

        for node in nodes:
            node.del_e_edges()

        #  НКА -> ДКА
        alphabet = self.get_alphabet()

        initial_state = frozenset({self.head})
        dfsm_states = {initial_state: FsmNode()}
        dfsm_head = dfsm_states[initial_state]

        queue = [initial_state]

        while queue:
            current_nfsm_state_set = queue.pop(0)
            current_dfsm_state = dfsm_states[current_nfsm_state_set]

            current_dfsm_state.exitable = any(node.exitable for node in current_nfsm_state_set)

            for symbol in alphabet:

                next_nfa_state_set = set()
                for nfa_state in current_nfsm_state_set:
                    if symbol in nfa_state.transitions:
                        for target_node in nfa_state.transitions[symbol]:
                            next_nfa_state_set.add(target_node)

                next_nfa_state_set = frozenset(next_nfa_state_set)

                if next_nfa_state_set and next_nfa_state_set not in dfsm_states:
                    dfsm_states[next_nfa_state_set] = FsmNode()
                    queue.append(next_nfa_state_set)

                if next_nfa_state_set:
                    current_dfsm_state.target(dfsm_states[next_nfa_state_set], symbol)

        self.head = dfsm_head

T = TypeVar("T")

class Stack(Generic[T]):

    def __init__(self) -> None:
        self.items: List[Type[T]] = []

    def is_empty(self) -> bool:
        return self.items == []

    def push(self, item: Type[T]) -> None:
        self.items.append(item)

    def pop(self) -> Type[T]:
        return self.items.pop()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.items} <- top)"


def is_barckets_balanced(template: str) -> bool:
    """
        Проверяет, что скобочная последовательность в строке верна.
    """
    stack = Stack()

    for char in template:
        if char == "(":
            stack.push(char)
        elif char == ")":
            if stack.is_empty():
                return False
            else:
                stack.pop()
    
    return stack.is_empty()


class Fsm(_Fsm):
    
    def __init__(self, pattern: str):

        if not is_barckets_balanced(pattern):
            raise Exception(f"В паттерне \"{pattern}\" со скобочками.")
        
        super().__init__(pattern)
