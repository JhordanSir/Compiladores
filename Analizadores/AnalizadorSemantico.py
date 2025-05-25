from AnalizadorLexico import analyze_file # Asumiendo que analyze_file está aquí
from analizadorSintactico import * # Esto debería importar Nodo, parser_ll1, cargar_tabla_desde_csv, y TOKENS_CON_LEXEMA
import tempfile
import os

# --- Definiciones de Symbol y ScopeManager (ya las tienes) ---
class Symbol:
    def __init__(self, name, data_type, scope_name, line_declared, symbol_type="variable"):
        self.name = name
        self.data_type = data_type
        self.scope_name = scope_name
        self.line_declared = line_declared
        self.symbol_type = symbol_type

    def __str__(self):
        return f"Symbol(Nombre: {self.name}, TipoDato: {self.data_type}, Ambito: {self.scope_name}, TipoSimbolo: {self.symbol_type}, Linea: {self.line_declared})"

class ScopeManager:
    def __init__(self):
        self.symbol_table = []
        self.scope_stack = []
        self.current_scope_name = None

    def enter_scope(self, name):
        self.scope_stack.append(name)
        self.current_scope_name = name
        # print(f"Debug Semantico: Entrando al ambito '{name}', Pila: {self.scope_stack}")

    def exit_scope(self):
        if self.scope_stack:
            exited_scope = self.scope_stack.pop()
            # print(f"Debug Semantico: Saliendo del ambito '{exited_scope}'")
            self.current_scope_name = self.scope_stack[-1] if self.scope_stack else None
        else:
            self.current_scope_name = None

    def add_symbol(self, symbol_name, data_type, line_declared, symbol_type="variable"):
        if not self.current_scope_name:
            print("Error Semántico: Intento de declarar símbolo fuera de cualquier ámbito.")
            return False
        for sym in self.symbol_table:
            if sym.name == symbol_name and sym.scope_name == self.current_scope_name:
                print(f"Error Semántico (Línea {line_declared}): Símbolo '{symbol_name}' ya declarado en el ámbito '{self.current_scope_name}'.")
                return False
        new_symbol = Symbol(symbol_name, data_type, self.current_scope_name, line_declared, symbol_type)
        self.symbol_table.append(new_symbol)
        return True

    def get_formatted_symbol_table(self):
        if not self.symbol_table:
            return "Tabla de Símbolos vacía."
        header = f"{'Nombre':<20} | {'Tipo de Dato':<15} | {'Ámbito':<20} | {'Tipo Símbolo':<15} | {'Línea Decl.':<10}"
        separator = "-" * (len(header) + 5)
        table_str = [header, separator]
        for sym in self.symbol_table:
            ambito_display = "global" if sym.scope_name == "global" else f"local ({sym.scope_name})"
            table_str.append(
                f"{sym.name:<20} | {sym.data_type:<15} | {ambito_display:<20} | {sym.symbol_type:<15} | {str(sym.line_declared):<10}"
            )
        return "\n".join(table_str)

# --- Función de Análisis Semántico (ajustada para tu AST) ---
# TOKENS_CON_LEXEMA debe ser importado de analizadorSintactico.py o definido aquí.
# Si no está definido, la siguiente línea es un ejemplo. ¡Asegúrate de que coincida con tu definición real!
# TOKENS_CON_LEXEMA = {'IDENTIFICADOR_TOKEN', 'QILLQA_TOKEN', 'YUPAY_TOKEN', 'CHIQI_KAY_TOKEN'}

def analizar_semantica_y_construir_tabla_simbolos(nodo_raiz, scope_manager):
    if nodo_raiz is None:
        return

    # Asegurarse que TOKENS_CON_LEXEMA está disponible.
    # Si no se importa correctamente, descomentar y ajustar la siguiente línea:
    # global TOKENS_CON_LEXEMA # O pasarlo como argumento a la función

    def get_node_value(node):
        if node is None: return "ERROR_NODO_NULO"
        if node.valor == 'IDENTIFICADOR_TOKEN' and node.hijos and node.hijos[0]:
            return node.hijos[0].valor
        return node.valor

    def get_node_line(node):
        if node and hasattr(node, 'token_original') and node.token_original:
            return node.token_original.lineno
        if node and node.valor == 'IDENTIFICADOR_TOKEN' and node.hijos and node.hijos[0] and \
           hasattr(node.hijos[0], 'token_original') and node.hijos[0].token_original:
            return node.hijos[0].token_original.lineno
        return "N/A"

    def extract_data_type_from_type_node(type_node_container):
        if type_node_container and type_node_container.valor == 'Type' and \
           type_node_container.hijos and type_node_container.hijos[0]:
            specific_type_node = type_node_container.hijos[0]
            raw_data_type = specific_type_node.valor
            if raw_data_type == 'TIPO_YUPAY': return 'yupay'
            if raw_data_type == 'TIPO_QILLQA': return 'qillqa'
            if raw_data_type == 'TIPO_CHIQIKAY': return 'chiqi kay'
            return raw_data_type
        return "desconocido"

    def visit(node):
        if node is None or node.valor == 'epsilon_node':
            return

        node_type = node.valor

        if node_type == 'Program':
            scope_manager.enter_scope("global")
            for hijo in node.hijos:
                visit(hijo)
            scope_manager.exit_scope()

        elif node_type == 'DefinitionList':
            if node.hijos and node.hijos[0].valor == 'PALABRA_RESERVADA_RURAY':
                if len(node.hijos) > 1: visit(node.hijos[1]) # OneDefinition
                if len(node.hijos) > 2: visit(node.hijos[2]) # DefinitionList (cola)
            # Si DefinitionList tiene otras producciones que llevan a OneDefinition (ej. para hatun_ruray)
            # y no empiezan con PALABRA_RESERVADA_RURAY, necesitarías manejarlas.
            # Basado en el AST, parece que OneDefinition es el nodo clave después de RURAY o HATUN_RURAY.
            # Si hatun_ruray está directamente bajo DefinitionList sin PALABRA_RESERVADA_RURAY,
            # se necesitaría otra condición aquí. Pero el AST sugiere que OneDefinition
            # es el que distingue entre ruray normal y hatun_ruray.

        elif node_type == 'OneDefinition':
            nombre_funcion = "error_nombre_funcion"
            linea_decl_func = "N/A"
            tipo_retorno_str = "void"
            parametros_node = None
            type_opt_node = None
            block_node = None

            if not node.hijos: return

            first_child_of_onedef = node.hijos[0]

            if first_child_of_onedef.valor == 'IDENTIFICADOR_TOKEN':
                nombre_funcion_node = first_child_of_onedef
                nombre_funcion = get_node_value(nombre_funcion_node)
                linea_decl_func = get_node_line(nombre_funcion_node)
                # Estructura para función normal: ID (0) '(' (1) ParamListOpt (2) ')' (3) TypeOpt (4) Block (5)
                if len(node.hijos) > 2 and node.hijos[2].valor == 'ParamListOpt': parametros_node = node.hijos[2]
                if len(node.hijos) > 4 and node.hijos[4].valor == 'TypeOpt': type_opt_node = node.hijos[4]
                if len(node.hijos) > 5 and node.hijos[5].valor == 'Block': block_node = node.hijos[5]

            elif first_child_of_onedef.valor == 'HATUN_RURAY_TOKEN':
                nombre_funcion = "hatun_ruray"
                linea_decl_func = get_node_line(first_child_of_onedef)
                # Estructura para hatun_ruray: HATUN_RURAY (0) '(' (1) ')' (2) Block (3)
                if len(node.hijos) > 3 and node.hijos[3].valor == 'Block': block_node = node.hijos[3]
            else:
                for hijo in node.hijos: visit(hijo)
                return

            if type_opt_node and type_opt_node.hijos and type_opt_node.hijos[0].valor == 'Type':
                tipo_retorno_str = extract_data_type_from_type_node(type_opt_node.hijos[0])

            scope_manager.add_symbol(nombre_funcion, tipo_retorno_str, linea_decl_func, symbol_type="funcion")
            scope_manager.enter_scope(nombre_funcion)

            if parametros_node and parametros_node.hijos and parametros_node.hijos[0].valor == 'ParamList':
                param_list_node = parametros_node.hijos[0]
                current_param_container = param_list_node
                while current_param_container and current_param_container.hijos and \
                      current_param_container.hijos[0].valor == 'Param':
                    param_node = current_param_container.hijos[0]
                    if len(param_node.hijos) == 3: # Type (0) ':' (1) ID (2)
                        param_type_container_node = param_node.hijos[0]
                        param_name_node = param_node.hijos[2]
                        param_name = get_node_value(param_name_node)
                        param_type_str = extract_data_type_from_type_node(param_type_container_node)
                        linea_decl_param = get_node_line(param_name_node)
                        scope_manager.add_symbol(param_name, param_type_str, linea_decl_param, symbol_type="parametro")
                    
                    if len(current_param_container.hijos) > 1 and current_param_container.hijos[1].valor == 'ParamTail':
                        param_tail_node = current_param_container.hijos[1]
                        # ParamTail -> COMA ParamList | epsilon
                        # El AST que mostraste es ParamTail -> epsilon o ParamTail -> (COMA) ParamList
                        # Si ParamTail tiene hijo y ese hijo es ParamList (o COMA y luego ParamList)
                        if param_tail_node.hijos and param_tail_node.hijos[0].valor == 'ParamList':
                             current_param_container = param_tail_node.hijos[0]
                        elif param_tail_node.hijos and len(param_tail_node.hijos) > 1 and param_tail_node.hijos[1].valor == 'ParamList': # Si hay COMA primero
                             current_param_container = param_tail_node.hijos[1]
                        else: break
                    else: break
            if block_node:
                visit(block_node)
            scope_manager.exit_scope()

        elif node_type == 'Block':
            if node.hijos and len(node.hijos) > 1 and node.hijos[1].valor == 'InstruccionesOpt':
                visit(node.hijos[1])

        elif node_type == 'InstruccionesOpt':
            if node.hijos and node.hijos[0].valor == 'Instruccion':
                visit(node.hijos[0])
                if len(node.hijos) > 1: visit(node.hijos[1])

        elif node_type == 'Instruccion':
            if node.hijos: visit(node.hijos[0])

        elif node_type == 'DeclaracionVariable':
            # VAR (0) ID (1) Type (2) InitOpt (3) ';' (4)
            if len(node.hijos) >= 3:
                identificador_node = node.hijos[1]
                type_container_node = node.hijos[2]
                if identificador_node.valor == 'IDENTIFICADOR_TOKEN' and type_container_node.valor == 'Type':
                    variable_name = get_node_value(identificador_node)
                    data_type_str = extract_data_type_from_type_node(type_container_node)
                    linea_declaracion = get_node_line(identificador_node)
                    scope_manager.add_symbol(variable_name, data_type_str, linea_declaracion, symbol_type="variable")
            if len(node.hijos) > 3 and node.hijos[3].valor == 'InicializacionOpt':
                visit(node.hijos[3])
        
        elif node_type in ['ParamListOpt', 'TypeOpt', 'InicializacionOpt', 'ParamTail', 'Param', 'Type']:
            for hijo in node.hijos:
                visit(hijo)
        
        elif node_type in ['PALABRA_RESERVADA_RURAY', 'IDENTIFICADOR_TOKEN', 'PARENTESIS_ABRE', 
                           'PARENTESIS_CIERRA', 'LLAVE_ABRE', 'LLAVE_CIERRA', 
                           'PALABRA_RESERVADA_VAR', 'PUNTO_Y_COMA_TOKEN',
                           'DOS_PUNTOS_TOKEN', 'HATUN_RURAY_TOKEN'] or \
             node_type.startswith('TIPO_'):
            pass # Nodos hoja o ya procesados por sus padres para la tabla de símbolos

        else:
            # print(f"Debug Semantico: Visitando nodo genérico/desconocido: {node_type}")
            for hijo in node.hijos:
                visit(hijo)
    
    # Antes de llamar a visit, asegúrate que TOKENS_CON_LEXEMA esté definido.
    # Esta es una verificación crucial. Si TOKENS_CON_LEXEMA no está en el ámbito global
    # (por ejemplo, si no se importó de analizadorSintactico.py), get_node_value fallará.
    if 'TOKENS_CON_LEXEMA' not in globals() and 'TOKENS_CON_LEXEMA' not in locals():
        print("Error Crítico: TOKENS_CON_LEXEMA no está definido. Esta variable es necesaria.")
        print("Asegúrate de que se importe de 'analizadorSintactico.py' o se defina globalmente.")
        # Podrías definir un default aquí como fallback, pero es mejor arreglar la importación/definición.
        # global TOKENS_CON_LEXEMA
        # TOKENS_CON_LEXEMA = {'IDENTIFICADOR_TOKEN'} # ¡ESTO ES SOLO UN FALLBACK PELIGROSO!
        # return # O salir si es un error irrecuperable

    visit(nodo_raiz)

# --- Función construir_arbol_sintactico (ya la tienes) ---
def construir_arbol_sintactico(codigo_fuente_str, ruta_tabla_csv, simbolo_inicial='Program'):
    lista_de_tokens = None
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ws", encoding='utf-8') as tmp_file:
            tmp_file.write(codigo_fuente_str)
            temp_file_path = tmp_file.name
        lista_de_tokens = analyze_file(temp_file_path) # De AnalizadorLexico.py
    except ImportError: # Específicamente para AnalizadorLexico.analyze_file
        print("Error Crítico: No se pudo importar 'AnalizadorLexico.analyze_file'.")
        return None
    except Exception as e:
        print(f"Error durante el análisis léxico o al procesar el archivo temporal: {e}")
        return None
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try: os.remove(temp_file_path)
            except OSError as e: print(f"Advertencia: No se pudo eliminar el archivo temporal {temp_file_path}: {e}")

    if lista_de_tokens is None:
        print("Error: El análisis léxico no produjo una lista de tokens.")
        return None
    
    tabla_parsing = cargar_tabla_desde_csv(ruta_tabla_csv) # De analizadorSintactico.py
    if tabla_parsing is None:
        return None
    
    arbol_sintactico_raiz = parser_ll1( # De analizadorSintactico.py
        lista_de_tokens,
        tabla_parsing,
        start_symbol=simbolo_inicial
    )
    return arbol_sintactico_raiz

# --- Función de depuración del AST (ya la tienes) ---
def debug_print_ast_structure(node, indent=0):
    if node is None: return
    # Intenta verificar si TOKENS_CON_LEXEMA está definido antes de usarlo
    lexema_str = ""
    try:
        if 'TOKENS_CON_LEXEMA' in globals() and node.valor in TOKENS_CON_LEXEMA and node.hijos and node.hijos[0]:
            lexema_str = f" (Lexema: {node.hijos[0].valor})"
    except NameError: # Si TOKENS_CON_LEXEMA no está definido
        pass # Simplemente no imprimas el lexema

    print("  " * indent + f"Nodo: {node.valor}{lexema_str} (Hijos: {len(node.hijos)})")
    
    for child in node.hijos:
        debug_print_ast_structure(child, indent + 1)


# --- Bloque Principal ---
if __name__ == "__main__":
    tabla_csv_path = "E:\\Compiladores\\Gramática\\tablitaTransiciones.csv"
    archivo_entrada_path = "E:\\Compiladores\\Inputs\\input1.ws"
    
    codigo_a_parsear = None
    try:
        with open(archivo_entrada_path, 'r', encoding='utf-8') as f_input:
            codigo_a_parsear = f_input.read()
        print(f"--- Contenido leído de '{archivo_entrada_path}' ---")
        if not codigo_a_parsear.strip():
            print("(El archivo está vacío o solo contiene espacios en blanco)")
        else:
            print(codigo_a_parsear.strip()) # .strip() para quitar líneas vacías extra al imprimir
        print("---------------------------------------------------")
    except FileNotFoundError:
        print(f"Error: El archivo de entrada '{archivo_entrada_path}' no fue encontrado.")
        exit(1)
    except Exception as e:
        print(f"Error al leer el archivo de entrada '{archivo_entrada_path}': {e}")
        exit(1)

    # 1. Construir el Árbol Sintáctico
    raiz_arbol = construir_arbol_sintactico(codigo_a_parsear, tabla_csv_path, simbolo_inicial='Program')
    
    if raiz_arbol:
        print("\n✅ Análisis sintáctico completado. Árbol generado.")
        
        # Descomenta para depurar la estructura del AST si es necesario
        # print("\n--- Estructura del AST (Debug) ---")
        # debug_print_ast_structure(raiz_arbol)
        # print("----------------------------------")

        # 2. Análisis Semántico y Tabla de Símbolos
        print("\n--- Iniciando Análisis Semántico y Construcción de Tabla de Símbolos ---")
        
        # Verificar que TOKENS_CON_LEXEMA está disponible globalmente
        # (debería ser importado por 'from analizadorSintactico import *')
        if 'TOKENS_CON_LEXEMA' not in globals():
            print("ALERTA CRÍTICA: La constante 'TOKENS_CON_LEXEMA' no está definida globalmente.")
            print("Esta constante es esencial para el análisis semántico y debe ser importada")
            print("desde 'analizadorSintactico.py' o definida en este archivo.")
            # Como fallback MUY BÁSICO, podrías definirla aquí, pero no es lo ideal:
            # global TOKENS_CON_LEXEMA
            # TOKENS_CON_LEXEMA = {'IDENTIFICADOR_TOKEN'} 
            # print("ADVERTENCIA: Usando una definición de TOKENS_CON_LEXEMA de fallback.")
        
        scope_manager = ScopeManager()
        analizar_semantica_y_construir_tabla_simbolos(raiz_arbol, scope_manager)
        
        print("\n--- Tabla de Símbolos Generada ---")
        print(scope_manager.get_formatted_symbol_table())
        
    else:
        print("\n❌ Falló el análisis sintáctico. No se generó el árbol, no se puede continuar con el análisis semántico.")