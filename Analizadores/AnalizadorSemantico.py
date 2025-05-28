# --- START OF FILE AnalizadorSemantico.py ---

from AnalizadorLexico import analyze_file
from analizadorSintactico import Nodo, parser_ll1, cargar_tabla_desde_csv, TOKENS_CON_LEXEMA

import tempfile
import os
import sys

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

    def __str__(self):
        param_str = f", Parametros: {[p for p in self.params]}" if self.symbol_type == "funcion" else ""
        status_str = ", Estado: " + ("Activo" if self.is_active else "Inactivo")
        value_str = ""
        if self.symbol_type in ["variable", "parametro"]:
            if self.value is not None:
                # Evitar mostrar placeholders como valores reales
                if isinstance(self.value, str) and self.value.startswith("<") and self.value.endswith(">"):
                     value_str = f", Valor: {self.value}" # Mostrar el placeholder
                elif isinstance(self.value, str): 
                    value_str = f", Valor: \"{self.value}\""
                elif isinstance(self.value, bool):
                     value_str = f", Valor: {'chiqaq' if self.value else 'mana_chiqap'}"
                else: 
                    value_str = f", Valor: {self.value}"
        
        return (f"Symbol(Nombre: {self.name}, TipoDato: {self.data_type}, Ambito: {self.scope_name}, "
                f"TipoSimbolo: {self.symbol_type}, Linea: {self.line_declared}{param_str}{status_str}{value_str})")

class ScopeManager:
    # ... (ScopeManager sin cambios respecto a la versión anterior con .is_active)
    def __init__(self):
        self.symbol_table = []
        self.scope_stack = ["global"] 
        self.current_scope_name = "global"
        self.error_list = [] 

    def log_error(self, message):
        self.error_list.append(message)

    def enter_scope(self, name):
        self.scope_stack.append(name)
        self.current_scope_name = name

    def exit_scope(self):
        if len(self.scope_stack) > 1: 
            exited_scope_name = self.scope_stack.pop()
            self.current_scope_name = self.scope_stack[-1]
            if exited_scope_name != "global":
                for sym in self.symbol_table:
                    if sym.scope_name == exited_scope_name:
                        sym.is_active = False

    def add_symbol(self, symbol_name, data_type, line_declared, symbol_type="variable", params=None, value=None):
        if not self.current_scope_name:
            self.log_error(f"Error Semántico Crítico (Línea {line_declared}): Intento de declarar símbolo '{symbol_name}' fuera de cualquier ámbito.")
            return None
        
        for sym in self.symbol_table:
            if sym.name == symbol_name and sym.scope_name == self.current_scope_name and sym.is_active:
                self.log_error(f"Error Semántico (Línea {line_declared}): Símbolo '{symbol_name}' ya declarado y activo en el ámbito '{self.current_scope_name}'.")
                return None
        
        new_symbol = Symbol(symbol_name, data_type, self.current_scope_name, line_declared, symbol_type, params, value)
        self.symbol_table.append(new_symbol)
        return new_symbol

    def lookup_symbol(self, name, line_used):
        for scope_name_in_stack in reversed(self.scope_stack):
            for sym in self.symbol_table:
                if sym.name == name and sym.scope_name == scope_name_in_stack and sym.is_active:
                    return sym 
        
        self.log_error(f"Error Semántico (Línea {line_used}): Símbolo '{name}' no ha sido declarado, no es accesible o no está activo en este ámbito.")
        return None

    def update_symbol_value(self, name, value, line_used):
        symbol = self.lookup_symbol(name, line_used) 
        if symbol:
            if symbol.symbol_type == "variable" or symbol.symbol_type == "parametro":
                # Actualizar solo si el nuevo valor no es un placeholder de no-literal,
                # o si el valor actual es None (primera asignación de un literal)
                is_placeholder = isinstance(value, str) and value.startswith("<") and value.endswith(">")
                if not is_placeholder or symbol.value is None:
                    symbol.value = value
            return True
        return False

    def get_formatted_symbol_table(self, show_only_active=False): # Nuevo parámetro
        if not self.symbol_table:
            return "Tabla de Símbolos vacía."
        
        # Filtrar símbolos si es necesario
        symbols_to_display = []
        if show_only_active:
            for sym in self.symbol_table:
                if sym.is_active:
                    symbols_to_display.append(sym)
        else:
            symbols_to_display = self.symbol_table

        if not symbols_to_display and show_only_active:
            return "No hay símbolos activos para mostrar."
        elif not symbols_to_display: # Tabla original vacía
            return "Tabla de Símbolos vacía."


        header = f"{'Nombre':<18} | {'Tipo Dato':<10} | {'Ámbito':<15} | {'Tipo Símb.':<12} | {'Línea':<5} | {'Params (Func)':<20} | {'Estado':<8} | {'Valor':<20}"
        separator = "-" * (len(header) + 7)
        table_str = [header, separator]

        for sym in symbols_to_display: # Usar la lista filtrada
            ambito_display = "global" if sym.scope_name == "global" else f"local ({sym.scope_name})"
            params_display = str([p for p in sym.params]) if sym.symbol_type == "funcion" else ""
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
            
            table_str.append(
                f"{sym.name:<18} | {sym.data_type:<10} | {ambito_display:<15} | {sym.symbol_type:<12} | {str(sym.line_declared):<5} | {params_display:<20} | {status_display:<8} | {value_display:<20}"
            )
        return "\n".join(table_str)

    def print_errors(self):
        if not self.error_list:
            print("\n✅ Análisis semántico completado sin errores.")
        else:
            print(f"\n❌ Análisis semántico completado con {len(self.error_list)} error(es):")
            for error in self.error_list:
                print(f"  - {error}")

# --- Función Principal de Análisis Semántico ---
def analizar_semantica_y_construir_tabla_simbolos(nodo_raiz, scope_manager):
    if nodo_raiz is None:
        return

    # --- Funciones Auxiliares Internas ---
    def get_node_value(node):
        if node is None: return None
        if node.valor in TOKENS_CON_LEXEMA and node.hijos and node.hijos[0]:
            return node.hijos[0].valor 
        return node.valor 

    def get_node_line(node):
        if node and hasattr(node, 'token_original') and node.token_original:
            return node.token_original.lineno
        if node and node.hijos: # Intenta obtener del primer hijo si el nodo actual no tiene
            if hasattr(node.hijos[0], 'token_original') and node.hijos[0].token_original:
                 return node.hijos[0].token_original.lineno
            for hijo in node.hijos: # Fallback recursivo
                line = get_node_line(hijo)
                if line != "N/A": return line
        return "N/A"

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
        return "desconocido"
    
    def extract_param_types_from_param_list(param_list_node):
        param_types = []
        if not (param_list_node and param_list_node.valor == 'ParamList' and \
                param_list_node.hijos and len(param_list_node.hijos) == 2 and \
                param_list_node.hijos[0].valor == 'Param' and \
                param_list_node.hijos[1].valor == 'ParamTail'):
            return param_types 
        current_P_node = param_list_node.hijos[0]
        current_PT_node = param_list_node.hijos[1]
        while True:
            if current_P_node.valor == 'Param' and len(current_P_node.hijos) == 3:
                param_type_container_node = current_P_node.hijos[0]
                param_type_str = extract_data_type_from_type_node(param_type_container_node)
                param_types.append(param_type_str)
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
        return param_types

    def evaluate_expression_for_literal_value(expression_node):
        """
        Recorre el subárbol de la expresión buscando un nodo Dato que contenga un literal.
        Devuelve el valor literal (int, float, str, bool) o un placeholder string.
        """
        if not expression_node or expression_node.valor != 'Expression':
            return "<expresión inválida>"

        # Contador para limitar la profundidad de la búsqueda y evitar bucles infinitos en ASTs malformados.
        # Y para detectar si la expresión es más que un simple literal.
        nodes_processed_for_value = 0
        
        # Usaremos una lista como pila para DFS manual, para tener más control.
        # Cada elemento de la pila será (nodo, profundidad)
        stack = [(expression_node, 0)]
        # Conjunto para evitar revisitar nodos en esta búsqueda específica (útil si hay ciclos o muchas ramas)
        # Esto es local a esta función de evaluación.
        visited_in_eval = set() 

        has_operators_or_calls = False

        while stack:
            current_node, depth = stack.pop()

            if current_node in visited_in_eval or depth > 10: # Limitar profundidad
                continue
            visited_in_eval.add(current_node)
            nodes_processed_for_value += 1

            # Detección temprana de complejidad (operadores, llamadas)
            if current_node.valor == 'ExpressionPrima' and current_node.hijos: has_operators_or_calls = True; break
            if current_node.valor == 'TermLogicoConti' and current_node.hijos: has_operators_or_calls = True; break
            if current_node.valor == 'FactorConti' and current_node.hijos: has_operators_or_calls = True; break
            if current_node.valor == 'ValorUnitario' and current_node.hijos: # ID o llamada
                # Si ValorUnitarioRest no es epsilon, es una llamada
                if len(current_node.hijos) > 1 and current_node.hijos[1].valor == 'ValorUnitarioRest' and current_node.hijos[1].hijos:
                    has_operators_or_calls = True; break 
                # Si es solo un ID, también cuenta como no literal en este contexto simple
                has_operators_or_calls = True; break # Considerar un ID solo como no literal aquí
            if current_node.valor == 'PARENTESIS_ABRE': # Expresión parentizada
                has_operators_or_calls = True; break


            if current_node.valor == 'Dato':
                if current_node.hijos:
                    literal_token_node = current_node.hijos[0]
                    if literal_token_node.valor in TOKENS_CON_LEXEMA:
                        if literal_token_node.hijos and literal_token_node.hijos[0]:
                            # Se encontró un literal antes de cualquier complejidad.
                            return literal_token_node.hijos[0].valor
                    elif literal_token_node.valor == 'CHIQAP_TOKEN_CHIQAQ': return True
                    elif literal_token_node.valor == 'CHIQAP_TOKEN_MANA_CHIQAQ': return False
            
            # Añadir hijos a la pila para DFS (en orden inverso para procesar el primero que se añade)
            if current_node.hijos:
                for child in reversed(current_node.hijos):
                    if child.valor != 'epsilon_node':
                        stack.append((child, depth + 1))
        
        if has_operators_or_calls:
            return "<expresión compleja>" # Si se detectó complejidad
        
        # Si se recorrió mucho sin encontrar un Dato literal simple.
        if nodes_processed_for_value > 1: # Si no es solo Expression -> ... -> Dato (1-2 nodos)
            return "<expresión no-literal>"
            
        return "<valor no determinado>" # Fallback

    # --- Función de Visita Principal ---
    def visit(node):
        # (La lógica de visit permanece igual que en la respuesta anterior,
        #  solo asegúrate que las llamadas a add_symbol y update_symbol_value
        #  usen el valor retornado por evaluate_expression_for_literal_value)

        if node is None or node.valor == 'epsilon_node':
            return

        node_type = node.valor

        if node_type == 'Program':
            if node.hijos and node.hijos[0].valor == 'DefinitionList':
                visit(node.hijos[0])
            else: 
                for hijo in node.hijos: visit(hijo)

        elif node_type == 'DefinitionList':
            if not node.hijos or (len(node.hijos) == 1 and node.hijos[0].valor == 'epsilon_node'):
                return
            first_child_node = node.hijos[0]
            if first_child_node.valor == 'PALABRA_RESERVADA_RURAY':
                if len(node.hijos) == 3:
                    visit(node.hijos[1]) 
                    visit(node.hijos[2]) 
                else: scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura DefinitionList (RURAY) inválida.")
            elif first_child_node.valor == 'PALABRA_RESERVADA_VAR': 
                if len(node.hijos) == 6:
                    identificador_node = node.hijos[1]
                    type_container_node = node.hijos[2]
                    inicializacion_opt_node = node.hijos[3]
                    
                    variable_name = get_node_value(identificador_node)
                    data_type_str = extract_data_type_from_type_node(type_container_node)
                    linea_declaracion = get_node_line(identificador_node)
                    initial_value = None

                    if inicializacion_opt_node.valor == 'InicializacionOpt' and inicializacion_opt_node.hijos:
                        if len(inicializacion_opt_node.hijos) == 2 and inicializacion_opt_node.hijos[1].valor == 'Expression':
                            expression_node_for_init = inicializacion_opt_node.hijos[1]
                            initial_value = evaluate_expression_for_literal_value(expression_node_for_init)
                            visit(expression_node_for_init) 
                    
                    scope_manager.add_symbol(variable_name, data_type_str, linea_declaracion, 
                                             symbol_type="variable", value=initial_value)
                    visit(node.hijos[5]) 
                else: scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura DefinitionList (VAR global) inválida.")

        elif node_type == 'OneDefinition':
            nombre_funcion, linea_decl_func, tipo_retorno_str, parametros_decl_node, block_node, es_hatun_ruray = "err", "N/A", "void", None, None, False
            param_types_list = []
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
                       type_opt_node.hijos and type_opt_node.hijos[0].valor == 'Type':
                        tipo_retorno_str = extract_data_type_from_type_node(type_opt_node.hijos[0])
                else: scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura OneDefinition (normal) inválida.")
            elif first_child_of_onedef.valor == 'HATUN_RURAY_TOKEN':
                nombre_funcion = "hatun_ruray"
                es_hatun_ruray = True
                linea_decl_func = get_node_line(first_child_of_onedef)
                if len(node.hijos) >= 4: block_node = node.hijos[3]
                else: scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura OneDefinition (hatun_ruray) inválida.")
            else: 
                for hijo in node.hijos: visit(hijo); return

            if not es_hatun_ruray and parametros_decl_node and parametros_decl_node.valor == 'ParamListOpt' and \
               parametros_decl_node.hijos and parametros_decl_node.hijos[0].valor == 'ParamList':
                param_types_list = extract_param_types_from_param_list(parametros_decl_node.hijos[0])

            if not es_hatun_ruray:
                scope_manager.add_symbol(nombre_funcion, tipo_retorno_str, linea_decl_func, 
                                         symbol_type="funcion", params=param_types_list)
            
            scope_manager.enter_scope(nombre_funcion)
            if parametros_decl_node and parametros_decl_node.valor == 'ParamListOpt' and \
               parametros_decl_node.hijos and parametros_decl_node.hijos[0].valor == 'ParamList':
                param_list_node = parametros_decl_node.hijos[0]
                if (param_list_node.hijos and len(param_list_node.hijos) == 2 and
                    param_list_node.hijos[0].valor == 'Param' and
                    param_list_node.hijos[1].valor == 'ParamTail'):
                    current_P_node = param_list_node.hijos[0]
                    current_PT_node = param_list_node.hijos[1]
                    while True:
                        if current_P_node.valor == 'Param' and len(current_P_node.hijos) == 3:
                            param_type_container_node = current_P_node.hijos[0]
                            param_name_node = current_P_node.hijos[2]
                            param_name = get_node_value(param_name_node)
                            param_type_str = extract_data_type_from_type_node(param_type_container_node)
                            linea_decl_param = get_node_line(param_name_node)
                            # Para parámetros, el valor inicial es None; se asignaría si se pasara por valor
                            # y tuviéramos una forma de evaluar las expresiones de los argumentos de llamada.
                            scope_manager.add_symbol(param_name, param_type_str, linea_decl_param, symbol_type="parametro", value=None)
                        else: break 
                        if current_PT_node.hijos and len(current_PT_node.hijos) == 3 and \
                           current_PT_node.hijos[0].valor == 'COMA_TOKEN' and \
                           current_PT_node.hijos[1].valor == 'Param' and \
                           current_PT_node.hijos[2].valor == 'ParamTail':
                            current_P_node = current_PT_node.hijos[1]
                            current_PT_node = current_PT_node.hijos[2]
                        else: break 
            if block_node: visit(block_node)
            scope_manager.exit_scope()

        elif node_type == 'DeclaracionVariable': 
            if len(node.hijos) == 5:
                identificador_node = node.hijos[1]
                type_container_node = node.hijos[2]
                inicializacion_opt_node = node.hijos[3]
                variable_name = get_node_value(identificador_node)
                data_type_str = extract_data_type_from_type_node(type_container_node)
                linea_declaracion = get_node_line(identificador_node)
                initial_value = None

                if inicializacion_opt_node.valor == 'InicializacionOpt' and inicializacion_opt_node.hijos:
                    if len(inicializacion_opt_node.hijos) == 2 and inicializacion_opt_node.hijos[1].valor == 'Expression':
                        expression_node_for_init = inicializacion_opt_node.hijos[1]
                        initial_value = evaluate_expression_for_literal_value(expression_node_for_init)
                        visit(expression_node_for_init)
                
                scope_manager.add_symbol(variable_name, data_type_str, linea_declaracion, 
                                         symbol_type="variable", value=initial_value)
            else: scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura DeclaracionVariable inválida.")

        elif node_type == 'AssignmentStmt':
            if len(node.hijos) == 4:
                identificador_node = node.hijos[0]
                expression_node = node.hijos[2]
                var_name = get_node_value(identificador_node)
                linea_uso = get_node_line(identificador_node)
                
                symbol = scope_manager.lookup_symbol(var_name, linea_uso) 
                if symbol and symbol.symbol_type == "funcion":
                    scope_manager.log_error(f"Error Semántico (Línea {linea_uso}): No se puede asignar un valor a la función '{var_name}'.")
                
                assigned_value = evaluate_expression_for_literal_value(expression_node)
                if symbol: 
                    scope_manager.update_symbol_value(var_name, assigned_value, linea_uso)
                
                visit(expression_node) 
            else: scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura AssignmentStmt inválida.")

        elif node_type == 'ValorUnitario':
            if node.hijos and node.hijos[0].valor == 'IDENTIFICADOR_TOKEN':
                id_node = node.hijos[0] 
                id_name = get_node_value(id_node) 
                linea_uso = get_node_line(id_node) 
                symbol = scope_manager.lookup_symbol(id_name, linea_uso) 
                
                is_function_call = (len(node.hijos) > 1 and node.hijos[1].valor == 'ValorUnitarioRest' and \
                                    node.hijos[1].hijos and node.hijos[1].hijos[0].valor == 'PARENTESIS_ABRE')

                if is_function_call:
                    if symbol and symbol.symbol_type != "funcion":
                        scope_manager.log_error(f"Error Semántico (Línea {linea_uso}): '{id_name}' no es una función y se está intentando llamar.")
                    elif symbol: 
                        if len(node.hijos[1].hijos) > 1 and node.hijos[1].hijos[1].valor == 'ArgumentosFuncionOpt':
                             visit(node.hijos[1].hijos[1]) 
                elif symbol and symbol.symbol_type == "funcion": 
                     scope_manager.log_error(f"Error Semántico (Línea {linea_uso}): Se usó el nombre de la función '{id_name}' como si fuera una variable. ¿Faltan paréntesis '()' para llamarla?")
            
            for hijo_idx, hijo_vu in enumerate(node.hijos):
                if hijo_idx == 0 and hijo_vu.valor == 'IDENTIFICADOR_TOKEN': 
                    if len(hijo_vu.hijos) > 0 and hijo_vu.hijos[0].valor not in TOKENS_CON_LEXEMA : visit(hijo_vu.hijos[0]) 
                else:
                    visit(hijo_vu)

        elif node_type == 'PrintStmt':
            if len(node.hijos) == 5 and node.hijos[2].valor == 'Expression': visit(node.hijos[2])
            else: 
                scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura PrintStmt inválida.")
                for hijo in node.hijos: visit(hijo)
        elif node_type == 'RetornoConValor':
             if len(node.hijos) == 3 and node.hijos[1].valor == 'Expression': visit(node.hijos[1])
             else:
                scope_manager.log_error(f"Error AST (Línea {get_node_line(node)}): Estructura RetornoConValor inválida.")
                for hijo in node.hijos: visit(hijo)
        elif node_type == 'ValorUnitarioRest': 
            if node.hijos and node.hijos[0].valor == 'PARENTESIS_ABRE': 
                if len(node.hijos) > 1 and node.hijos[1].valor == 'ArgumentosFuncionOpt':
                    visit(node.hijos[1]) 
        elif node_type in ['Block', 'InstruccionesOpt', 'Instruccion', 'InicializacionOpt', 
                           'Expression', 'TermLogico', 'TermComparacion', 'Factor', 'Unidad', 'Dato',
                           'ExpressionPrima', 'TermLogicoConti', 'TermComparacionConti', 'FactorConti',
                           'ArgumentosFuncionOpt', 'MasArgumentosFuncion',
                           'Estructura_If', 'ElseOpcional', 'ManaSichusBloque', 'ArgumentosElseIf',
                           'Bucle', 'ForLoop', 'LoopInitialization', 'AsignacionBucle', 'AsignacionBucleDato',
                           'ExpressionOpt', 'LoopUpdateOpt', 'IncrementoStmt', 'Incremento',
                           'ParamListOpt', 'ParamList', 'Param', 'ParamTail', 'TypeOpt', 'Type',
                           'MulOp', 'OpcionLogico', 'OpcionComparacion',
                           'Retorno', 'RetornoSinValor']:
            for hijo in node.hijos:
                visit(hijo)
        
        elif node_type.endswith('_TOKEN') or node_type.startswith('PALABRA_RESERVADA_') or \
             node_type.startswith('TIPO_') or node_type.startswith('OPERADOR_') or \
             node_type in ['PARENTESIS_ABRE', 'PARENTESIS_CIERRA', 'LLAVE_ABRE', 'LLAVE_CIERRA',
                            'COMA_TOKEN', 'PUNTO_Y_COMA_TOKEN', 'DOS_PUNTOS_TOKEN', '$',
                            'MulOpPacha', 'MulOpRakiy', 'MulOpModulo', 'MulOpSum', 'MulOpRes', 
                            'OpcionLogicoWan', 'OpcionLogicoUtaq', 
                            'OpcionComparacionIgual', 'OpcionComparacionNoIgual', 
                            'OpcionComparacionMenor', 'OpcionComparacionMayor', 
                            'OpcionComparacionMenorIgual', 'OpcionComparacionMayorIgual',
                            'IncrementoOpPlus', 'IncrementoOpMinus'
                            ]:
            pass 
        else: 
            for hijo in node.hijos: 
                visit(hijo)
    
    visit(nodo_raiz)


# --- Funciones para construir el AST y ejecutar ---
def construir_arbol_sintactico(codigo_fuente_str, ruta_tabla_csv, simbolo_inicial='Program'):
    lista_de_tokens = None
    temp_file_path = None
    # original_stdout = sys.stdout 
    # null_out = open(os.devnull, 'w')
    # sys.stdout = null_out
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ws", encoding='utf-8') as tmp_file:
            tmp_file.write(codigo_fuente_str)
            temp_file_path = tmp_file.name
        lista_de_tokens = analyze_file(temp_file_path)
    except ImportError:
        # sys.stdout = original_stdout
        # null_out.close()
        print("Error Crítico: No se pudo importar 'AnalizadorLexico.analyze_file'.")
        return None
    except Exception as e:
        # sys.stdout = original_stdout
        # null_out.close()
        print(f"Error durante el análisis léxico o al procesar el archivo temporal: {e}")
        return None
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try: os.remove(temp_file_path)
            except OSError: pass 
    # sys.stdout = original_stdout 
    # null_out.close()
    if lista_de_tokens is None:
        print("Error: El análisis léxico no produjo una lista de tokens.")
        return None
    tabla_parsing = cargar_tabla_desde_csv(ruta_tabla_csv)
    if tabla_parsing is None:
        print("Error: La tabla de parsing no pudo ser cargada.")
        return None
    # original_stdout = sys.stdout
    # null_out = open(os.devnull, 'w')
    # sys.stdout = null_out
    arbol_sintactico_raiz = parser_ll1(
        lista_de_tokens,
        tabla_parsing,
        start_symbol=simbolo_inicial
    )
    # sys.stdout = original_stdout
    # null_out.close()
    return arbol_sintactico_raiz

# --- Bloque Principal ---
if __name__ == "__main__":
    tabla_csv_path = "E:\\Compiladores\\Gramática\\tablitaTransiciones.csv" 
    archivo_entrada_path = "E:\\Compiladores\\Inputs\\input1.ws" 
    
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

    raiz_arbol = construir_arbol_sintactico(codigo_fuente_str=codigo_a_parsear, ruta_tabla_csv=tabla_csv_path)
    
    if raiz_arbol:
        print("\n--- Iniciando Análisis Semántico ---")
        if 'TOKENS_CON_LEXEMA' not in globals():
             print("ALERTA CRÍTICA: 'TOKENS_CON_LEXEMA' no está definido globalmente.")
        
        scope_manager = ScopeManager()
        analizar_semantica_y_construir_tabla_simbolos(raiz_arbol, scope_manager)
        
        print("\n--- Tabla de Símbolos Completa (Incluye Inactivos) ---")
        print(scope_manager.get_formatted_symbol_table()) # Llama sin filtro

        print("\n--- Tabla de Símbolos (Solo Activos al Final del Análisis) ---")
        print(scope_manager.get_formatted_symbol_table(show_only_active=True)) # Llama con filtro
        
        scope_manager.print_errors()
        
    else:
        print("\n❌ Falló el análisis sintáctico. No se generó el árbol.")