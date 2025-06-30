from AnalizadorLexico import *
from analizadorSintactico import *
import sys
import tempfile
import os
import sys
import copy
sys.setrecursionlimit(2147483647)

_CURRENT_FUNCTION_RETURN_VALUE = None
_IS_RETURNING = False
_IS_BREAKING_LOOP = False 

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class ActivationNode:
    def __init__(self, name, parent=None, args=None):
        self.name = name
        self.parent = parent
        self.children = []
        self.args = args if args is not None else []
        self.id = f"node_{id(self)}"

class ActivationTreeBuilder:
    def __init__(self):
        self.root = None
        self.current_node = None

    def enter_function(self, name, args):
        new_node = ActivationNode(name, parent=self.current_node, args=args)
        if self.root is None:
            self.root = new_node
        
        if self.current_node:
            self.current_node.children.append(new_node)
        
        self.current_node = new_node

    def exit_function(self):
        if self.current_node:
            self.current_node = self.current_node.parent

    def to_graphviz(self):
        if not self.root:
            return "digraph G {}"
        
        dot_lines = [
            "digraph G {",
            '    graph [bgcolor="#f0f0f0", fontname="Helvetica"];',
            '    node [shape=ellipse, style=filled, fillcolor="#ffcccc", color="#d12b2b", fontname="Helvetica", penwidth=2];',
            '    edge [color="#d12b2b", penwidth=2];'
        ]
        
        def build_dot_recursive(node):
            arg_list_str = []
            for arg in node.args:
                if isinstance(arg, str):
                    arg_list_str.append(f'"{arg}"')
                else:
                    arg_list_str.append(str(arg))
            arg_str = ', '.join(arg_list_str)

            label = f"{node.name}({arg_str})"
            if node.name == "hatun_ruray" and not node.args:
                label = "hatun_ruray"

            dot_lines.append(f'    {node.id} [label="{label}"];')
            
            for child in node.children:
                dot_lines.append(f'    {node.id} -> {child.id};')
                build_dot_recursive(child)
        
        build_dot_recursive(self.root)
        dot_lines.append("}")
        return "\n".join(dot_lines)

class Symbol:
    def __init__(self, name, data_type, scope_name, line_declared, symbol_type="variable", params=None, value=None):
        self.name = name
        self.data_type = data_type 
        self.scope_name = scope_name
        self.line_declared = line_declared
        self.symbol_type = symbol_type  
        self.params = params if params is not None else []  
        self.is_active = True
        self.value = value  
        self.ast_node = None 
        self.param_list_ast_node = None 

    def __str__(self):
        param_str = ""
        if self.symbol_type == "funcion":
            param_details = [f"{p['name']}:{p['type']}" for p in self.params]
            param_str = f", Parametros: [{', '.join(param_details)}]"

        status_str = ", Estado: " + ("Activo" if self.is_active else "Inactivo")
        value_str = ""
        if self.symbol_type in ["variable", "parametro"]:
            if self.value is not None:
                if isinstance(self.value, str) and self.value.startswith("<") and self.value.endswith(">"):
                    value_str = f", Valor: {self.value}"
                elif isinstance(self.value, str):
                    value_str = f", Valor: \"{self.value}\""
                elif isinstance(self.value, bool):
                    value_str = f", Valor: {'chiqaq' if self.value else 'mana_chiqap'}"
                else:
                    value_str = f", Valor: {self.value}"
        
        return (f"Symbol(Nombre: {self.name}, TipoDato: {self.data_type}, Ambito: {self.scope_name}, "
                f"TipoSimbolo: {self.symbol_type}, Linea: {self.line_declared}{param_str}{status_str}{value_str})")

class ScopeManager:
    def __init__(self):
        self.symbol_table = []
        self.scope_stack = ["global"] 
        self.current_scope_name = "global"
        self.error_list = []
        self.symbol_table_history = [] 
        self.loop_level = 0 

    def log_error(self, message):
        self.error_list.append(message)

    def enter_scope(self, name_prefix):
        scope_name = f"{name_prefix}_{len(self.scope_stack)}"
        self.scope_stack.append(scope_name)
        self.current_scope_name = scope_name

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            exited_scope_name = self.scope_stack.pop()
            self.current_scope_name = self.scope_stack[-1]
            self.symbol_table_history.append(copy.deepcopy(self.symbol_table))
            if exited_scope_name != "global": 
                for sym in self.symbol_table:
                    if sym.scope_name == exited_scope_name:
                        sym.is_active = False
    
    def enter_loop(self):
        self.loop_level += 1
        self.enter_scope("loop") 

    def exit_loop(self):
        self.exit_scope() 
        self.loop_level -= 1
        
    def is_inside_loop(self):
        return self.loop_level > 0

    def add_symbol(self, symbol_name, data_type, line_declared, symbol_type="variable", params=None, value=None, ast_node=None, param_list_ast_node=None):
        if not self.current_scope_name:
            self.log_error(f"Error Semántico Crítico (Línea {line_declared}): Intento de declarar símbolo '{symbol_name}' fuera de cualquier ámbito.")
            return None
        
        for sym in self.symbol_table:
            if sym.name == symbol_name and sym.scope_name == self.current_scope_name and sym.is_active:
                self.log_error(f"Error Semántico (Línea {line_declared}): Símbolo '{symbol_name}' ya declarado y activo en el ámbito '{self.current_scope_name}'.")
                return None
        
        new_symbol = Symbol(symbol_name, data_type, self.current_scope_name, line_declared, symbol_type, params, value)
        if symbol_type == "funcion":
            new_symbol.ast_node = ast_node
            new_symbol.param_list_ast_node = param_list_ast_node
        self.symbol_table.append(new_symbol)
        return new_symbol

    def lookup_symbol(self, name, line_used):
        for scope_name_in_stack in reversed(self.scope_stack):
            for sym in self.symbol_table:
                if sym.name == name and sym.scope_name == scope_name_in_stack and sym.is_active:
                    return sym
        
        self.log_error(f"Error Semántico (Línea {line_used}): Símbolo '{name}' no ha sido declarado o no es accesible en este ámbito.")
        return None

    def update_symbol_value(self, name, value, line_used):
        symbol = self.lookup_symbol(name, line_used)
        if symbol:
            if symbol.symbol_type == "variable" or symbol.symbol_type == "parametro":
                symbol.value = value
            elif symbol.symbol_type == "funcion":
                 self.log_error(f"Error Semántico (Línea {line_used}): No se puede asignar un valor directamente a una función '{name}'.")
                 return False
            return True
        return False

    def format_symbol_table(self, table_to_format, title="Tabla de Símbolos"):
        if not table_to_format:
            return f"{title}\nTabla de Símbolos vacía."
        
        header = f"{'Nombre':<18} | {'Tipo Dato':<10} | {'Ámbito':<25} | {'Tipo Símb.':<12} | {'Línea':<5} | {'Params (Func)':<30} | {'Estado':<8} | {'Valor':<20}"
        separator = "-" * (len(header) + 15)
        table_str_list = [f"\n--- {title} ---", header, separator]

        for sym in table_to_format:
            ambito_display = sym.scope_name
            params_display = ""
            if sym.symbol_type == "funcion":
                param_details = [f"{p['name']}:{p['type']}" for p in sym.params]
                params_display = ', '.join(param_details)

            status_display = "Activo" if sym.is_active else "Inactivo"
            value_display = "---"
            if sym.symbol_type in ["variable", "parametro"]:
                if sym.value is not None:
                    if isinstance(sym.value, str) and sym.value.startswith("<") and sym.value.endswith(">"):
                        value_display = sym.value
                    elif isinstance(sym.value, str):
                        value_display = f"\"{sym.value}\""
                    elif isinstance(sym.value, bool):
                        value_display = "chiqaq" if sym.value else "mana_chiqap"
                    else:
                        value_display = str(sym.value)
            
            table_str_list.append(
                f"{sym.name:<18} | {sym.data_type:<10} | {ambito_display:<25} | {sym.symbol_type:<12} | {str(sym.line_declared):<5} | {params_display:<30} | {status_display:<8} | {value_display:<20}"
            )
        return "\n".join(table_str_list)

    def print_errors(self):
        if not self.error_list:
            print("\n✅ Análisis semántico completado sin errores.")
        else:
            print(f"\n❌ Análisis semántico completado con {len(self.error_list)} error(es):")
            for error in self.error_list:
                print(f"  - {error}")

def get_node_value(node):
    if node is None: return None
    if node.valor in TOKENS_CON_LEXEMA and node.hijos and node.hijos[0]:
        return node.hijos[0].valor
    return node.valor

def get_node_line(node):
    if node and hasattr(node, 'token_original') and node.token_original:
        return node.token_original.lineno
    if node and node.hijos:
        for hijo in node.hijos:
            if hasattr(hijo, 'token_original') and hijo.token_original:
                return hijo.token_original.lineno
            if isinstance(hijo, Nodo):
                line = get_node_line(hijo)
                if line != "N/A":
                    return line
    return "N/A"

def get_literal_value_from_dato_node(dato_node, scope_manager, line_num):
    if dato_node and dato_node.hijos:
        literal_token_node = dato_node.hijos[0]
        raw_value = get_node_value(literal_token_node)
        
        if literal_token_node.valor == 'YUPAY_TOKEN': return int(raw_value)
        if literal_token_node.valor == 'CHIQI_KAY_TOKEN': return float(raw_value)
        if literal_token_node.valor == 'QILLQA_TOKEN': return str(raw_value)
        if literal_token_node.valor == 'CHIQAP_TOKEN_CHIQAQ': return True
        if literal_token_node.valor == 'CHIQAP_TOKEN_MANA_CHIQAQ': return False
    scope_manager.log_error(f"Error Semántico (Línea {line_num}): Tipo de dato literal desconocido o malformado.")
    return None

def evaluate_expression(expression_node, scope_manager, tree_builder):
    if not expression_node or expression_node.valor != 'Expression':
        scope_manager.log_error(f"Error Interno: evaluate_expression llamado con nodo inválido: {expression_node.valor if expression_node else 'None'}")
        return "<expresión inválida>"
    
    val1 = evaluate_term_logico(expression_node.hijos[0], scope_manager, tree_builder)

    expression_prima_node = expression_node.hijos[1]
    if expression_prima_node.hijos and expression_prima_node.hijos[0].valor != 'epsilon_node':
        current_expr_prima_node = expression_prima_node
        while current_expr_prima_node.hijos and current_expr_prima_node.hijos[0].valor != 'epsilon_node':
            op_logico_node = current_expr_prima_node.hijos[0] 
            term_logico2_node = current_expr_prima_node.hijos[1]
            
            val2 = evaluate_term_logico(term_logico2_node, scope_manager, tree_builder)

            if not isinstance(val1, bool) or not isinstance(val2, bool):
                line = get_node_line(op_logico_node)
                scope_manager.log_error(f"Error Semántico (Línea {line}): Operador lógico aplicado a tipos no booleanos ('{type(val1).__name__}', '{type(val2).__name__}').")
                return "<error tipo op lógico>"

            op_type_node = op_logico_node.hijos[0] 
            op_type = op_type_node.hijos[0].valor  

            if op_type == 'OPERADOR_LOGICO_UTAQ': val1 = val1 or val2
            elif op_type == 'OPERADOR_LOGICO_WAN': val1 = val1 and val2
            else:
                scope_manager.log_error(f"Error Semántico (Línea {get_node_line(op_logico_node)}): Operador lógico desconocido '{op_type}'.")
                return "<error op lógico desconocido>"
            
            current_expr_prima_node = current_expr_prima_node.hijos[2] 
    return val1

def evaluate_term_logico(term_logico_node, scope_manager, tree_builder):
    val1 = evaluate_term_comparacion(term_logico_node.hijos[0], scope_manager, tree_builder)

    term_logico_conti_node = term_logico_node.hijos[1]
    if term_logico_conti_node.hijos and term_logico_conti_node.hijos[0].valor != 'epsilon_node':
        current_term_logico_conti_node = term_logico_conti_node
        while current_term_logico_conti_node.hijos and current_term_logico_conti_node.hijos[0].valor != 'epsilon_node':
            op_comp_node = current_term_logico_conti_node.hijos[0] 
            term_comp2_node = current_term_logico_conti_node.hijos[1]

            val2 = evaluate_term_comparacion(term_comp2_node, scope_manager, tree_builder)
            
            op_type_node = op_comp_node.hijos[0] 
            op_type = op_type_node.hijos[0].valor 

            if type(val1) != type(val2) and not (isinstance(val1, (int, float)) and isinstance(val2, (int, float))):
                if not (isinstance(val1, str) and isinstance(val2, str)): 
                    line = get_node_line(op_comp_node)
                    scope_manager.log_error(f"Error Semántico (Línea {line}): Comparación entre tipos incompatibles ('{type(val1).__name__}' y '{type(val2).__name__}').")
                    return "<error tipo comparación>"
            try:
                if op_type == 'OPERADOR_IGUALDAD': val1 = val1 == val2 
                elif op_type == 'OPERADOR_MANA_IGUAL': val1 = val1 != val2
                else: 
                    if not (isinstance(val1, (int, float, str)) and isinstance(val2, (int, float, str))):
                        line = get_node_line(op_comp_node)
                        scope_manager.log_error(f"Error Semántico (Línea {line}): Operadores de orden solo aplican a números o strings, no a '{type(val1).__name__}' y '{type(val2).__name__}'.")
                        return "<error tipo orden>"
                    if op_type == 'OPERADOR_MAYOR': val1 = val1 > val2
                    elif op_type == 'OPERADOR_MENOR': val1 = val1 < val2
                    elif op_type == 'OPERADOR_MAYOR_IGUAL': val1 = val1 >= val2
                    elif op_type == 'OPERADOR_MENOR_IGUAL': val1 = val1 <= val2
                    else:
                        scope_manager.log_error(f"Error Semántico (Línea {get_node_line(op_comp_node)}): Operador de comparación desconocido '{op_type}'.")
                        return "<error op comparación desconocido>"
            except TypeError: 
                line = get_node_line(op_comp_node)
                scope_manager.log_error(f"Error Semántico (Línea {line}): No se puede aplicar el operador de orden entre '{type(val1).__name__}' y '{type(val2).__name__}'.")
                return "<error tipo orden>"
            
            current_term_logico_conti_node = current_term_logico_conti_node.hijos[2] 
    return val1

def evaluate_term_comparacion(term_comparacion_node, scope_manager, tree_builder):
    current_value = evaluate_sumaresta_term(term_comparacion_node.hijos[0], scope_manager, tree_builder)
    
    next_sumaresta_conti_node = term_comparacion_node.hijos[1]
    while next_sumaresta_conti_node.hijos and next_sumaresta_conti_node.hijos[0].valor != 'epsilon_node':
        op_node = next_sumaresta_conti_node.hijos[0]      
        term_node = next_sumaresta_conti_node.hijos[1]     
        next_sumaresta_conti_node = next_sumaresta_conti_node.hijos[2] 

        next_value = evaluate_sumaresta_term(term_node, scope_manager, tree_builder)
        operator = op_node.hijos[0].valor 

        if operator == 'OPERADOR_MAS':
            if isinstance(current_value, (int, float)) and isinstance(next_value, (int, float)):
                current_value += next_value
            elif isinstance(current_value, str) and isinstance(next_value, str): 
                current_value += next_value
            elif isinstance(current_value, str) and isinstance(next_value, (int, float, bool)):
                current_value += str(next_value)
            elif isinstance(current_value, (int, float, bool)) and isinstance(next_value, str):
                current_value = str(current_value) + next_value
            else:
                scope_manager.log_error(f"Error Semántico (Línea {get_node_line(op_node)}): Operador '+' con tipos incompatibles ('{type(current_value).__name__}', '{type(next_value).__name__}').")
                return "<error de tipo en suma>"
        elif operator == 'OPERADOR_MENOS':
            if isinstance(current_value, (int, float)) and isinstance(next_value, (int, float)):
                current_value -= next_value
            else:
                scope_manager.log_error(f"Error Semántico (Línea {get_node_line(op_node)}): Operador '-' con tipo no numérico ('{type(current_value).__name__}', '{type(next_value).__name__}').")
                return "<error de tipo en resta>"
        else:
            scope_manager.log_error(f"Error Semántico (Línea {get_node_line(op_node)}): Operador '{operator}' desconocido en SumaRestaConti.")
            return "<error de operador en suma/resta>"
            
    return current_value

def evaluate_sumaresta_term(sumaresta_term_node, scope_manager, tree_builder):
    current_value = evaluate_factor(sumaresta_term_node.hijos[0], scope_manager, tree_builder)

    next_muldivmod_conti_node = sumaresta_term_node.hijos[1]
    while next_muldivmod_conti_node.hijos and next_muldivmod_conti_node.hijos[0].valor != 'epsilon_node':
        op_node = next_muldivmod_conti_node.hijos[0]   
        factor_node = next_muldivmod_conti_node.hijos[1] 
        next_muldivmod_conti_node = next_muldivmod_conti_node.hijos[2]

        next_value = evaluate_factor(factor_node, scope_manager, tree_builder)
        operator = op_node.hijos[0].valor 

        if not (isinstance(current_value, (int, float)) and isinstance(next_value, (int, float))):
            scope_manager.log_error(f"Error Semántico (Línea {get_node_line(op_node)}): Operación mul/div/mod con tipo no numérico ('{type(current_value).__name__}', '{type(next_value).__name__}').")
            return "<error de tipo en mul/div/mod>"

        if operator == 'OPERADOR_PACHA': current_value *= next_value
        elif operator == 'OPERADOR_RAKI':
            if next_value == 0:
                scope_manager.log_error(f"Error Semántico (Línea {get_node_line(op_node)}): División por cero.")
                return "<división por cero>"
            current_value /= next_value 
        elif operator == 'OPERADOR_MODULO':
            if next_value == 0:
                scope_manager.log_error(f"Error Semántico (Línea {get_node_line(op_node)}): Módulo por cero.")
                return "<módulo por cero>"
            current_value %= next_value
        else:
            scope_manager.log_error(f"Error Semántico (Línea {get_node_line(op_node)}): Operador '{operator}' desconocido en MulDivModConti.")
            return "<error de operador en mul/div/mod>"
    return current_value

def evaluate_factor(factor_node, scope_manager, tree_builder):
    is_negative = False
    actual_node_to_eval = factor_node.hijos[0]
    
    if factor_node.hijos[0].valor == 'OPERADOR_MENOS':
        is_negative = True
        actual_node_to_eval = factor_node.hijos[1]
        
    value = evaluate_unidad(actual_node_to_eval, scope_manager, tree_builder)

    if is_negative:
        if not isinstance(value, (int, float)):
            scope_manager.log_error(f"Error Semántico (Línea {get_node_line(factor_node)}): Operador unario '-' aplicado a valor no numérico '{value}'.")
            return "<error tipo negación>"
        return -value
    return value

def evaluate_unidad(unidad_node, scope_manager, tree_builder):
    child = unidad_node.hijos[0]
    line_num = get_node_line(unidad_node)

    if child.valor == 'Dato':
        return get_literal_value_from_dato_node(child, scope_manager, line_num)
    
    elif child.valor == 'ValorUnitario':
        id_node = child.hijos[0]
        identifier_name = get_node_value(id_node)
        line_num_id = get_node_line(id_node)
        valor_unitario_rest_node = child.hijos[1]

        if valor_unitario_rest_node.hijos and valor_unitario_rest_node.hijos[0].valor == 'PARENTESIS_ABRE':
            return execute_function_call(identifier_name, valor_unitario_rest_node, scope_manager, line_num_id, tree_builder)
        else: 
            symbol = scope_manager.lookup_symbol(identifier_name, line_num_id)
            if symbol:
                if symbol.value is None and not (isinstance(symbol.value, str) and symbol.value.startswith("<")):
                    scope_manager.log_error(f"Error Semántico (Línea {line_num_id}): Variable '{identifier_name}' usada antes de ser inicializada con un valor concreto.")
                    return f"<variable '{identifier_name}' no inicializada>"
                return symbol.value
            return f"<variable '{identifier_name}' no declarada>"

    elif child.valor == 'PARENTESIS_ABRE':
        return evaluate_expression(unidad_node.hijos[1], scope_manager, tree_builder)
    
    scope_manager.log_error(f"Error Semántico (Línea {line_num}): No se pudo evaluar el nodo Unidad '{child.valor}'.")
    return "<error en Unidad>"

def execute_function_call(func_name, valor_unitario_rest_node, scope_manager, line_call, tree_builder):
    global _CURRENT_FUNCTION_RETURN_VALUE, _IS_RETURNING 
    
    func_symbol = scope_manager.lookup_symbol(func_name, line_call)
    if not func_symbol: return f"<función '{func_name}' no definida>"
    if func_symbol.symbol_type != "funcion":
        scope_manager.log_error(f"Error Semántico (Línea {line_call}): '{func_name}' no es una función.")
        return f"<'{func_name}' no es función>"

    arg_values = []
    if valor_unitario_rest_node and len(valor_unitario_rest_node.hijos) > 1 and valor_unitario_rest_node.hijos[1].valor == 'ArgumentosFuncionOpt':
        argumentos_funcion_opt_node = valor_unitario_rest_node.hijos[1]
        if argumentos_funcion_opt_node.hijos and argumentos_funcion_opt_node.hijos[0].valor != 'epsilon_node':
            current_expr_node = argumentos_funcion_opt_node.hijos[0]
            mas_args_node = argumentos_funcion_opt_node.hijos[1]
            while True:
                arg_val = evaluate_expression(current_expr_node, scope_manager, tree_builder)
                arg_values.append(arg_val)
                if mas_args_node.hijos and mas_args_node.hijos[0].valor != 'epsilon_node':
                    current_expr_node = mas_args_node.hijos[1]
                    mas_args_node = mas_args_node.hijos[2]
                else: break

    if len(arg_values) != len(func_symbol.params):
        scope_manager.log_error(f"Error Semántico (Línea {line_call}): Función '{func_name}' esperaba {len(func_symbol.params)} argumento(s), recibió {len(arg_values)}.")
        return f"<error args '{func_name}'>"

    if not func_symbol.ast_node:
        scope_manager.log_error(f"Error Interno: No se encontró el AST para la función '{func_name}'.")
        return f"<error AST func '{func_name}'>"
    
    tree_builder.enter_function(func_name, arg_values)
    
    returned_value_from_this_call = None
    try:
        outer_is_returning = _IS_RETURNING
        outer_return_value = _CURRENT_FUNCTION_RETURN_VALUE

        _IS_RETURNING = False 
        _CURRENT_FUNCTION_RETURN_VALUE = None

        function_scope_name = f"func_call_{func_name}_{line_call}_{len(scope_manager.scope_stack)}"
        scope_manager.enter_scope(function_scope_name)

        for i, param_info in enumerate(func_symbol.params):
            arg_value_coerced = arg_values[i]
            if param_info['type'] == 'yupay' and isinstance(arg_value_coerced, float):
                arg_value_coerced = int(arg_value_coerced)
            scope_manager.add_symbol(param_info['name'], param_info['type'], param_info['line'], 
                                    symbol_type="parametro", value=arg_value_coerced)
        
        analizar_semantica_y_construir_tabla_simbolos(func_symbol.ast_node, scope_manager, tree_builder, is_function_execution=True)

        if not _IS_RETURNING and func_symbol.data_type != "void":
            scope_manager.log_error(f"Error Semántico (Línea {line_call}): La función '{func_name}' debe retornar un valor de tipo '{func_symbol.data_type}', pero puede terminar sin una instrucción 'kutipay'.")

        returned_value_from_this_call = _CURRENT_FUNCTION_RETURN_VALUE 
        
        scope_manager.exit_scope() 
        
        _IS_RETURNING = outer_is_returning
        _CURRENT_FUNCTION_RETURN_VALUE = outer_return_value
    
    finally:
        tree_builder.exit_function()
    
    return returned_value_from_this_call

def analizar_semantica_y_construir_tabla_simbolos(nodo_raiz, scope_manager, tree_builder, is_function_execution=False): 
    if nodo_raiz is None:
        return

    def extract_data_type_from_type_node(type_node_container):
        if type_node_container and type_node_container.valor == 'Type' and \
           type_node_container.hijos and type_node_container.hijos[0]:
            specific_type_node = type_node_container.hijos[0]
            raw_data_type = specific_type_node.valor
            if raw_data_type == 'TIPO_YUPAY': return 'yupay'
            if raw_data_type == 'TIPO_QILLQA': return 'qillqa'
            if raw_data_type == 'TIPO_CHIQI': return 'chiqi'
            if raw_data_type == 'TIPO_CHIQAP': return 'chiqap'
            return raw_data_type
        return "void" 

    def extract_param_details_from_param_list(param_list_node):
        param_details_list = []
        if not (param_list_node and param_list_node.valor == 'ParamList' and \
                param_list_node.hijos and len(param_list_node.hijos) == 2 and \
                param_list_node.hijos[0].valor == 'Param' and \
                param_list_node.hijos[1].valor == 'ParamTail'):
            return param_details_list
        
        current_P_node = param_list_node.hijos[0]
        current_PT_node = param_list_node.hijos[1]
        while True:
            if current_P_node.valor == 'Param' and len(current_P_node.hijos) == 3:
                param_type_container_node = current_P_node.hijos[0] 
                param_name_node = current_P_node.hijos[2]          
                
                param_name = get_node_value(param_name_node)
                param_type_str = extract_data_type_from_type_node(param_type_container_node)
                linea_decl_param = get_node_line(param_name_node)
                param_details_list.append({'name': param_name, 'type': param_type_str, 'line': linea_decl_param})
            else: break 
            
            if current_PT_node.hijos and len(current_PT_node.hijos) == 3 and \
               current_PT_node.hijos[0].valor == 'COMA_TOKEN' and \
               current_PT_node.hijos[1].valor == 'Param' and \
               current_PT_node.hijos[2].valor == 'ParamTail':
                current_P_node = current_PT_node.hijos[1]
                current_PT_node = current_PT_node.hijos[2]
            elif not current_PT_node.hijos or \
                 (len(current_PT_node.hijos) == 1 and current_PT_node.hijos[0].valor == 'epsilon_node'):
                break 
            else: break
        return param_details_list

    def visit_node_recursive(node):
        global _IS_RETURNING, _CURRENT_FUNCTION_RETURN_VALUE, _IS_BREAKING_LOOP
        nonlocal is_function_execution

        if node is None or node.valor == 'epsilon_node': return
        if (_IS_RETURNING and is_function_execution): return
        if (_IS_BREAKING_LOOP and scope_manager.is_inside_loop()): return

        node_type = node.valor

        if node_type == 'Program':
            for hijo in node.hijos: visit_node_recursive(hijo)

        elif node_type == 'DefinitionList':
            if not node.hijos or (len(node.hijos) == 1 and node.hijos[0].valor == 'epsilon_node'):
                return
            first_child_valor = node.hijos[0].valor
            if first_child_valor == 'PALABRA_RESERVADA_RURAY':
                one_definition_node = node.hijos[1]
                visit_node_recursive(one_definition_node)
                next_definition_list_node = node.hijos[2]
                visit_node_recursive(next_definition_list_node)
            elif first_child_valor == 'PALABRA_RESERVADA_VAR':
                identificador_node = node.hijos[1]
                type_container_node = node.hijos[2]
                inicializacion_opt_node = node.hijos[3]
                variable_name = get_node_value(identificador_node)
                data_type_str = extract_data_type_from_type_node(type_container_node)
                linea_declaracion = get_node_line(identificador_node)
                initial_value = None
                if inicializacion_opt_node.hijos and inicializacion_opt_node.hijos[0].valor != 'epsilon_node':
                    expression_node = inicializacion_opt_node.hijos[1]
                    initial_value = evaluate_expression(expression_node, scope_manager, tree_builder)
                    if data_type_str == 'yupay' and isinstance(initial_value, float):
                        initial_value = int(initial_value)
                scope_manager.add_symbol(variable_name, data_type_str, linea_declaracion, 
                                         symbol_type="variable", value=initial_value)
                next_definition_list_node = node.hijos[5]
                visit_node_recursive(next_definition_list_node)

        elif node_type == 'OneDefinition':
            nombre_funcion, linea_decl_func, tipo_retorno_str = "err", "N/A", "void"
            parametros_decl_node, block_node, es_hatun_ruray = None, None, False
            param_details_list = [] 
            if not node.hijos: return
            first_child_of_onedef = node.hijos[0]
            if first_child_of_onedef.valor == 'IDENTIFICADOR_TOKEN':
                nombre_funcion_node = first_child_of_onedef
                nombre_funcion = get_node_value(nombre_funcion_node)
                linea_decl_func = get_node_line(nombre_funcion_node)
                if len(node.hijos) >= 6:
                    parametros_decl_node = node.hijos[2] 
                    type_opt_node = node.hijos[4]       
                    block_node = node.hijos[5]         
                    if type_opt_node and type_opt_node.valor == 'TypeOpt' and \
                       type_opt_node.hijos and type_opt_node.hijos[0].valor != 'epsilon_node' and \
                       type_opt_node.hijos[0].valor == 'Type': 
                        tipo_retorno_str = extract_data_type_from_type_node(type_opt_node.hijos[0])
                    else: 
                        tipo_retorno_str = "void" 
                else: scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura OneDefinition (normal) inválida.")
            elif first_child_of_onedef.valor == 'HATUN_RURAY_TOKEN':
                nombre_funcion = "hatun_ruray"
                es_hatun_ruray = True
                linea_decl_func = get_node_line(first_child_of_onedef)
                tipo_retorno_str = "void" 
                if len(node.hijos) >= 4:
                     block_node = node.hijos[3] 
                     parametros_decl_node = Nodo('ParamListOpt') 
                     parametros_decl_node.agregar_hijo(Nodo('epsilon_node'))
                else: scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura OneDefinition (hatun_ruray) inválida.")
            else: 
                for hijo in node.hijos: visit_node_recursive(hijo)
                return
            if parametros_decl_node and parametros_decl_node.valor == 'ParamListOpt' and \
               parametros_decl_node.hijos and parametros_decl_node.hijos[0].valor == 'ParamList':
                param_details_list = extract_param_details_from_param_list(parametros_decl_node.hijos[0])
            scope_manager.add_symbol(nombre_funcion, tipo_retorno_str, linea_decl_func, 
                                     symbol_type="funcion", params=param_details_list,
                                     ast_node=block_node, param_list_ast_node=parametros_decl_node)

        elif node_type == 'Block':
            if node.hijos and len(node.hijos) > 1: 
                 visit_node_recursive(node.hijos[1])

        elif node_type == 'InstruccionesOpt':
            if node.hijos and node.hijos[0].valor != 'epsilon_node':
                visit_node_recursive(node.hijos[0]) 
                if (_IS_RETURNING and is_function_execution) or \
                   (_IS_BREAKING_LOOP and scope_manager.is_inside_loop()): return 
                visit_node_recursive(node.hijos[1]) 
        
        elif node_type == 'DeclaracionVariable': 
            if len(node.hijos) >= 5:
                identificador_node = node.hijos[1]
                type_container_node = node.hijos[2]
                inicializacion_opt_node = node.hijos[3]
                variable_name = get_node_value(identificador_node)
                data_type_str = extract_data_type_from_type_node(type_container_node)
                linea_declaracion = get_node_line(identificador_node)
                initial_value = None 
                if inicializacion_opt_node.valor == 'InicializacionOpt' and inicializacion_opt_node.hijos and \
                   len(inicializacion_opt_node.hijos) == 2 and inicializacion_opt_node.hijos[1].valor == 'Expression':
                    expression_node_for_init = inicializacion_opt_node.hijos[1]
                    initial_value = evaluate_expression(expression_node_for_init, scope_manager, tree_builder)
                    if data_type_str == 'yupay' and isinstance(initial_value, float):
                        initial_value = int(initial_value) 
                    type_of_value = type(initial_value).__name__
                    is_compatible = False
                    if data_type_str == 'yupay' and isinstance(initial_value, int): is_compatible = True
                    elif data_type_str == 'chiqi' and isinstance(initial_value, (int, float)): is_compatible = True
                    elif data_type_str == 'qillqa' and isinstance(initial_value, str): is_compatible = True
                    elif data_type_str == 'chiqap' and isinstance(initial_value, bool): is_compatible = True
                    if not is_compatible:
                        scope_manager.log_error(f"Error Semántico (Línea {linea_declaracion}): Incompatibilidad de tipos. No se puede asignar un valor de tipo '{type_of_value}' a una variable de tipo '{data_type_str}'.")
                scope_manager.add_symbol(variable_name, data_type_str, linea_declaracion, 
                                         symbol_type="variable", value=initial_value)
            else: scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura DeclaracionVariable inválida.")

        elif node_type == 'IdBasedStmt':
            identificador_node = node.hijos[0]
            rest_node = node.hijos[1]
            var_name = get_node_value(identificador_node)
            linea = get_node_line(identificador_node)
            rest_first_child = rest_node.hijos[0]
            if rest_first_child.valor == 'OPERADOR_ASIGNACION':
                symbol = scope_manager.lookup_symbol(var_name, linea)
                if not symbol: return
                expression_node = rest_node.hijos[1]
                assigned_value = evaluate_expression(expression_node, scope_manager, tree_builder)
                if symbol.data_type == 'yupay' and isinstance(assigned_value, float):
                    assigned_value = int(assigned_value) 
                type_of_value = type(assigned_value).__name__
                is_compatible = False
                if symbol.data_type == 'yupay' and isinstance(assigned_value, int): is_compatible = True
                elif symbol.data_type == 'chiqi' and isinstance(assigned_value, (int, float)): is_compatible = True
                elif symbol.data_type == 'qillqa' and isinstance(assigned_value, str): is_compatible = True
                elif symbol.data_type == 'chiqap' and isinstance(assigned_value, bool): is_compatible = True
                if not is_compatible:
                    scope_manager.log_error(f"Error Semántico (Línea {linea}): Incompatibilidad de tipos. No se puede asignar un valor de tipo '{type_of_value}' a la variable '{var_name}' de tipo '{symbol.data_type}'.")
                else:
                    scope_manager.update_symbol_value(var_name, assigned_value, linea)
            elif rest_first_child.valor == 'Incremento':
                symbol = scope_manager.lookup_symbol(var_name, linea)
                if not symbol: return
                op_node = rest_first_child.hijos[0]
                if not isinstance(symbol.value, (int, float)):
                    scope_manager.log_error(f"Error Semántico (Línea {linea}): El operador '++' o '--' solo se puede aplicar a yupay o chiqi, no a '{symbol.data_type}'.")
                    return
                new_value = symbol.value
                if op_node.valor == 'IncrementoOpPlus':
                    new_value += 1
                elif op_node.valor == 'IncrementoOpMinus':
                    new_value -= 1
                scope_manager.update_symbol_value(var_name, new_value, linea)
            elif rest_first_child.valor == 'PARENTESIS_ABRE':
                execute_function_call(var_name, rest_node, scope_manager, linea, tree_builder)

        elif node_type == 'RetornoConValor': 
            if not is_function_execution:
                scope_manager.log_error(f"Error Semántico (Línea {get_node_line(node)}): 'kutipay' fuera de una función.")
            else:
                if len(node.hijos) == 3 and node.hijos[1].valor == 'Expression':
                    expression_node = node.hijos[1]
                    return_value = evaluate_expression(expression_node, scope_manager, tree_builder)
                    _CURRENT_FUNCTION_RETURN_VALUE = return_value
                    _IS_RETURNING = True
                else: scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura RetornoConValor inválida.")
        
        elif node_type == 'RetornoSinValor': 
            if scope_manager.is_inside_loop():
                _IS_BREAKING_LOOP = True
            elif is_function_execution:
                _CURRENT_FUNCTION_RETURN_VALUE = None 
                _IS_RETURNING = True
            else:
                 scope_manager.log_error(f"Error Semántico (Línea {get_node_line(node)}): 'pakiy' fuera de una función o bucle.")
        
        elif node_type == 'PrintStmt':
            argument_list_opt_node = node.hijos[2]
            values_to_print = []
            if argument_list_opt_node.hijos and argument_list_opt_node.hijos[0].valor != 'epsilon_node':
                current_expression_node = argument_list_opt_node.hijos[0]
                current_tail_node = argument_list_opt_node.hijos[1]
                while True:
                    value = evaluate_expression(current_expression_node, scope_manager, tree_builder)
                    values_to_print.append(value)
                    if current_tail_node.hijos and current_tail_node.hijos[0].valor != 'epsilon_node':
                        current_expression_node = current_tail_node.hijos[1]
                        current_tail_node = current_tail_node.hijos[2]
                    else:
                        break
            output_str = []
            for val in values_to_print:
                if isinstance(val, bool):
                    output_str.append("chiqaq" if val else "mana_chiqap")
                elif val is None:
                    output_str.append("nulo")
                else:
                    output_str.append(str(val))
            print(" ".join(output_str))

        elif node_type == 'IfStmt':
            condition_node = node.hijos[2]
            block_node = node.hijos[4]
            else_part_node = node.hijos[5]
            condition_value = evaluate_expression(condition_node, scope_manager, tree_builder)
            if not isinstance(condition_value, bool):
                scope_manager.log_error(f"Error Semántico (Línea {get_node_line(condition_node)}): La condición del 'sichus' debe ser booleana, se obtuvo '{type(condition_value).__name__}'.")
            else:
                if condition_value: 
                    scope_manager.enter_scope("if_block")
                    visit_node_recursive(block_node)
                    scope_manager.exit_scope()
                else: 
                    visit_node_recursive(else_part_node)

        elif node_type == 'ElsePart':
            if node.hijos and node.hijos[0].valor != 'epsilon_node':
                if node.hijos[0].valor == 'PALABRA_RESERVADA_MANA':
                    block_node = node.hijos[1]
                    scope_manager.enter_scope("else_block")
                    visit_node_recursive(block_node)
                    scope_manager.exit_scope()
                elif node.hijos[0].valor == 'PALABRA_RESERVADA_MANA_SICHUS':
                    args_elseif_opt_node = node.hijos[1]
                    elseif_block_node = node.hijos[2]
                    next_else_part_node = node.hijos[3]
                    condition_value_elseif = True 
                    if args_elseif_opt_node.hijos and args_elseif_opt_node.hijos[0].valor != 'epsilon_node':
                        elseif_condition_node = args_elseif_opt_node.hijos[1]
                        condition_value_elseif = evaluate_expression(elseif_condition_node, scope_manager, tree_builder)
                        if not isinstance(condition_value_elseif, bool):
                             scope_manager.log_error(f"Error Semántico (Línea {get_node_line(elseif_condition_node)}): La condición del 'mana_sichus' debe ser booleana.")
                             condition_value_elseif = False 
                    if condition_value_elseif:
                        scope_manager.enter_scope("elseif_block")
                        visit_node_recursive(elseif_block_node)
                        scope_manager.exit_scope()
                    else:
                        visit_node_recursive(next_else_part_node) 
        
        elif node_type == 'ForLoop':
            init_node = node.hijos[2]
            condition_opt_node = node.hijos[4] 
            update_opt_node = node.hijos[6]
            loop_block_node = node.hijos[8]
            outer_is_breaking = _IS_BREAKING_LOOP 
            scope_manager.enter_loop()
            if init_node.hijos and init_node.hijos[0].valor != 'epsilon_node':
                visit_node_recursive(init_node) 
            _IS_BREAKING_LOOP = False 
            while True:
                condition_value = True 
                if condition_opt_node.hijos and condition_opt_node.hijos[0].valor != 'epsilon_node':
                    condition_node = condition_opt_node.hijos[0]
                    condition_value = evaluate_expression(condition_node, scope_manager, tree_builder)
                    if not isinstance(condition_value, bool):
                        scope_manager.log_error(f"Error Semántico (Línea {get_node_line(condition_node)}): La condición del bucle 'para' debe ser booleana.")
                        break 
                if not condition_value:
                    break 
                visit_node_recursive(loop_block_node) 
                if _IS_BREAKING_LOOP:
                    break 
                if _IS_RETURNING and is_function_execution: 
                    scope_manager.exit_loop()
                    _IS_BREAKING_LOOP = outer_is_breaking 
                    return 
                if update_opt_node.hijos and update_opt_node.hijos[0].valor != 'epsilon_node':
                    visit_node_recursive(update_opt_node) 
            scope_manager.exit_loop() 
            _IS_BREAKING_LOOP = outer_is_breaking

        elif node_type == 'LoopInitialization':
            if node.hijos and node.hijos[0].valor != 'epsilon_node':
                visit_node_recursive(node.hijos[0]) 
        
        elif node_type == 'DeclaracionVariableSimple':
            identificador_node = node.hijos[1]
            type_container_node = node.hijos[2]
            expression_node = node.hijos[4]
            var_name = get_node_value(identificador_node)
            data_type = extract_data_type_from_type_node(type_container_node)
            linea = get_node_line(identificador_node)
            value = evaluate_expression(expression_node, scope_manager, tree_builder)
            if data_type == 'yupay' and isinstance(value, float):
                value = int(value) 
            type_of_value = type(value).__name__
            is_compatible = False
            if data_type == 'yupay' and isinstance(value, int): is_compatible = True
            elif data_type == 'chiqi' and isinstance(value, (int, float)): is_compatible = True
            elif data_type == 'qillqa' and isinstance(value, str): is_compatible = True
            elif data_type == 'chiqap' and isinstance(value, bool): is_compatible = True
            if not is_compatible:
                scope_manager.log_error(f"Error Semántico (Línea {linea}): Incompatibilidad de tipos. No se puede asignar un valor de tipo '{type_of_value}' a una variable de tipo '{data_type}'.")
            scope_manager.add_symbol(var_name, data_type, linea, "variable", value=value)

        elif node_type == 'AssignmentStmtSimple':
            identificador_node = node.hijos[0]
            expression_node = node.hijos[2]
            var_name = get_node_value(identificador_node)
            linea = get_node_line(identificador_node)
            value = evaluate_expression(expression_node, scope_manager, tree_builder)
            symbol = scope_manager.lookup_symbol(var_name, linea)
            if symbol and symbol.data_type == 'yupay' and isinstance(value, float):
                value = int(value)
            scope_manager.update_symbol_value(var_name, value, linea)

        elif node_type == 'LoopUpdateOpt': 
            if node.hijos and node.hijos[0].valor != 'epsilon_node':
                visit_node_recursive(node.hijos[0]) 

        elif node_type == 'LoopUpdateStmt':
            identificador_node = node.hijos[0]
            rest_node = node.hijos[1]
            var_name = get_node_value(identificador_node)
            linea = get_node_line(identificador_node)
            first_child_of_rest = rest_node.hijos[0]
            if first_child_of_rest.valor == 'OPERADOR_ASIGNACION':
                symbol = scope_manager.lookup_symbol(var_name, linea)
                if not symbol: return
                expression_node = rest_node.hijos[1]
                assigned_value = evaluate_expression(expression_node, scope_manager, tree_builder)
                if symbol.data_type == 'yupay' and isinstance(assigned_value, float):
                    assigned_value = int(assigned_value)
                scope_manager.update_symbol_value(var_name, assigned_value, linea)
            elif first_child_of_rest.valor == 'Incremento':
                symbol = scope_manager.lookup_symbol(var_name, linea)
                if not symbol: return
                op_node = first_child_of_rest.hijos[0]
                if not isinstance(symbol.value, (int, float)):
                    scope_manager.log_error(f"Error Semántico (Línea {linea}): El operador '++' o '--' solo se puede aplicar a yupay o chiqi, no a '{symbol.data_type}'.")
                    return
                new_value = symbol.value
                if op_node.valor == 'IncrementoOpPlus': new_value += 1
                elif op_node.valor == 'IncrementoOpMinus': new_value -= 1
                scope_manager.update_symbol_value(var_name, new_value, linea)
            elif first_child_of_rest.valor == 'PARENTESIS_ABRE':
                execute_function_call(var_name, rest_node, scope_manager, linea, tree_builder)

        elif node_type in ['Instruccion', 'Estructura_If', 'Bucle', 'LoopDeclOrAssign', 'ExpressionOpt', 'Incremento', 'IncrementoOpPlus', 'IncrementoOpMinus', 'ArgumentosElseIfOpt', 'LoopUpdateStmtRest']:
            if (_IS_RETURNING and is_function_execution) or (_IS_BREAKING_LOOP and scope_manager.is_inside_loop()): return
            for hijo in node.hijos:
                visit_node_recursive(hijo)
                if (_IS_RETURNING and is_function_execution) or (_IS_BREAKING_LOOP and scope_manager.is_inside_loop()): break 
        else:
            if (_IS_RETURNING and is_function_execution) or (_IS_BREAKING_LOOP and scope_manager.is_inside_loop()): return
            for hijo in node.hijos: 
                visit_node_recursive(hijo)
                if (_IS_RETURNING and is_function_execution) or (_IS_BREAKING_LOOP and scope_manager.is_inside_loop()): break
    
    visit_node_recursive(nodo_raiz)

def construir_arbol_sintactico(codigo_fuente_str, ruta_tabla_csv, simbolo_inicial='Program'):
    lista_de_tokens = None
    temp_file_path = None
    original_stdout = sys.stdout 

    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ws", encoding='utf-8') as tmp_file:
            tmp_file.write(codigo_fuente_str)
            temp_file_path = tmp_file.name
        
        lista_de_tokens = analyze_file(temp_file_path) 
    
    except ImportError:
        sys.stdout = original_stdout 
        print("Error Crítico: No se pudo importar 'AnalizadorLexico.analyze_file'.")
        return None
    except Exception as e:
        sys.stdout = original_stdout
        print(f"Error durante el análisis léxico o al procesar el archivo temporal: {e}")
        return None
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try: os.remove(temp_file_path)
            except OSError: pass 
    
    sys.stdout = original_stdout 
    
    if lista_de_tokens is None:
        print("Error: El análisis léxico no produjo una lista de tokens.")
        return None

    tabla_parsing = cargar_tabla_desde_csv(ruta_tabla_csv)
    if tabla_parsing is None:
        print("Error: La tabla de parsing no pudo ser cargada.")
        return None

    arbol_sintactico_raiz = parser_ll1(
        lista_de_tokens,
        tabla_parsing,
        start_symbol=simbolo_inicial
    )
    return arbol_sintactico_raiz

if __name__ == "__main__":
    tabla_csv_path = os.path.join(BASE_DIR, "Gramática", "tablitaTransiciones.csv")
    archivo_entrada_path = os.path.join(BASE_DIR, "Inputs", "input2.wasi")
    
    codigo_a_parsear = None
    try:
        with open(archivo_entrada_path, 'r', encoding='utf-8') as f_input:
            codigo_a_parsear = f_input.read()
    except FileNotFoundError:
        print(f"Error: El archivo de entrada '{archivo_entrada_path}' no fue encontrado.")
        exit(1)
    except Exception as e:
        print(f"Error al leer el archivo de entrada '{archivo_entrada_path}': {e}")
        exit(1)

    if not codigo_a_parsear.strip():
        print("El código fuente está vacío o solo contiene espacios en blanco.")
        exit(1)

    raiz_arbol_sintactico = construir_arbol_sintactico(codigo_fuente_str=codigo_a_parsear, ruta_tabla_csv=tabla_csv_path)
    
    if raiz_arbol_sintactico:
        scope_manager = ScopeManager()
        tree_builder = ActivationTreeBuilder()

        print("--- Fase 1: Análisis y Declaración de Símbolos ---")
        analizar_semantica_y_construir_tabla_simbolos(raiz_arbol_sintactico, scope_manager, tree_builder)
        
        print(scope_manager.format_symbol_table(scope_manager.symbol_table, 
                                                title="Tabla de Símbolos Post-Declaración"))
        
        print("-" * 50)

        print("\n--- Fase 3: Generación de Árbol de Activación ---")
        dot_code = tree_builder.to_graphviz()
        output_dot_path = os.path.join(BASE_DIR, "Salida Graphviz", "arbol_activacion.txt")
        try:
            os.makedirs(os.path.dirname(output_dot_path), exist_ok=True)
            with open(output_dot_path, 'w', encoding='utf-8') as f:
                f.write(dot_code)
            print(f"✅ Árbol de activación guardado en: {output_dot_path}")
            print("   Para generar la imagen, usa el comando: dot -Tpng {ruta_a_dot} -o arbol.png".format(ruta_a_dot=output_dot_path))
        except Exception as e:
            print(f"❌ Error al guardar el archivo .txt: {e}")

        print("-" * 50)

        print("\n--- Reporte Final ---")
        def filter_hatun_ruray(symbol_list):
            return [s for s in symbol_list if not (s.name == "hatun_ruray" and s.symbol_type == "funcion")]

        final_symbol_table_snapshot_all = copy.deepcopy(scope_manager.symbol_table)
        final_symbol_table_filtered = filter_hatun_ruray(final_symbol_table_snapshot_all)
        print(scope_manager.format_symbol_table(final_symbol_table_filtered, 
                                                title="Tabla de Símbolos COMPLETA (sin hatun_ruray)"))

        active_symbols_final_all = [s for s in scope_manager.symbol_table if s.is_active]
        active_symbols_final_filtered = filter_hatun_ruray(active_symbols_final_all)
        print(scope_manager.format_symbol_table(active_symbols_final_filtered, title="Tabla de Símbolos SÓLO ACTIVOS (sin hatun_ruray)"))

        print("-" * 50)
        
        print("\n--- Fase 2: Ejecución (Salida de Consola) ---")
        
        hatun_ruray_symbol = None
        for sym in scope_manager.symbol_table:
            if sym.name == "hatun_ruray" and sym.symbol_type == "funcion":
                hatun_ruray_symbol = sym
                break
        
        if hatun_ruray_symbol:
            _IS_RETURNING = False
            _CURRENT_FUNCTION_RETURN_VALUE = None
            _IS_BREAKING_LOOP = False
            
            execute_function_call(
                func_name="hatun_ruray",
                valor_unitario_rest_node=None,
                scope_manager=scope_manager,
                line_call=hatun_ruray_symbol.line_declared,
                tree_builder=tree_builder
            )
        else:
            print("Advertencia: No se encontró la función principal 'hatun_ruray'. No se ejecutó nada.")

        scope_manager.print_errors()
        
    else:
        print("\n❌ Falló el análisis sintáctico o léxico. No se generó el árbol.")