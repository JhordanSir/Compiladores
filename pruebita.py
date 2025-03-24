import ply.lex as lex

# Tabla 1: Lexemas WayraSimi
tokens = [
    'YUPAY_TOKEN',  # Número, Decimal
    'CHIQAP_TOKEN', # Booleano
    'QILLQA_TOKEN', # Texto, Letra
    'CHIQAQP_TOKEN', # Verdad, Realidad
    'IDENTIFICADOR_TOKEN', # Variable, function_1
    'OPERADOR_MAS', # +
    'OPERADOR_MENOS', # -
    'OPERADOR_PACHA', # *
    'OPERADOR_RAKI', # /
    'OPERADOR_MODULO', # %
    'OPERADOR_ASIGNACION', # =
    'OPERADOR_IGUALDAD', # ==
    'OPERADOR_MANA_IGUAL', # !=
    'OPERADOR_MENOR', # <
    'OPERADOR_MAYOR', # >
    'OPERADOR_MENOR_IGUAL', # <=
    'OPERADOR_MAYOR_IGUAL', # >=
    'OPERADOR_LOGICO_WAN', # and
    'OPERADOR_LOGICO_UTAQ', # or
    'OPERADOR_LOGICO_MANA', # not
    'PARENTESIS_ABRE', # (
    'PARENTESIS_CIERRA', # )
    'LLAVE_ABRE', # {
    'LLAVE_CIERRA', # }
    'CORCHETE_ABRE', # [
    'CORCHETE_CIERRA', # ]
    'COMA_TOKEN', # ,
    'PUNTO_TOKEN', # .
    'DOS_PUNTOS_TOKEN', # :
    'PUNTO_Y_COMA_TOKEN', # ;
    'COMENTARIO_TOKEN_LINEA', # # ...
    'COMENTARIO_TOKEN_BLOQUE_ABRE', # /*
    'COMENTARIO_TOKEN_BLOQUE_CIERRA', # */
    'PALABRA_RESERVADA_SICHUS', # sichus
    'PALABRA_RESERVADA_MANA_SICHUS', # mana sichus
    'PALABRA_RESERVADA_MANA', # mana
    'PALABRA_RESERVADA_PARA', # para
    'PALABRA_RESERVADA_RURAY', # ruray
    'PALABRA_RESERVADA_KUTIPAY', # kutipay
    'PALABRA_RESERVADA_IMPRIMIY', # imprimiy
    'PALABRA_RESERVADA_AYLLU', # ayllu
    'PALABRA_RESERVADA_VAR', # variable
    'PALABRA_RESERVADA_TAKYAQ', # takyaq
    'CADENA_TOKEN' # String literals
]

# Regular expressions for simple tokens
t_OPERADOR_MAS    = r'\+'
t_OPERADOR_MENOS   = r'-'
t_OPERADOR_PACHA   = r'\*'
t_OPERADOR_RAKI    = r'/'
t_OPERADOR_MODULO  = r'%'
t_OPERADOR_ASIGNACION = r'='
t_OPERADOR_IGUALDAD = r'=='
t_OPERADOR_MANA_IGUAL = r'!='
t_OPERADOR_MENOR   = r'<'
t_OPERADOR_MAYOR   = r'>'
t_OPERADOR_MENOR_IGUAL = r'<='
t_OPERADOR_MAYOR_IGUAL = r'>='
t_OPERADOR_LOGICO_WAN = r'wan'
t_OPERADOR_LOGICO_UTAQ = r'utaq'
t_OPERADOR_LOGICO_MANA = r'mana'
t_PARENTESIS_ABRE  = r'\('
t_PARENTESIS_CIERRA = r'\)'
t_LLAVE_ABRE       = r'\{'
t_LLAVE_CIERRA      = r'\}'
t_CORCHETE_ABRE    = r'\['
t_CORCHETE_CIERRA   = r'\]'
t_COMA_TOKEN       = r','
t_PUNTO_TOKEN      = r'\.'
t_DOS_PUNTOS_TOKEN = r':'
t_PUNTO_Y_COMA_TOKEN = r';'
t_PALABRA_RESERVADA_SICHUS = r'sichus'
t_PALABRA_RESERVADA_MANA_SICHUS = r'mana\s+sichus' # Handle space between mana and sichus
t_PALABRA_RESERVADA_MANA = r'mana'
t_PALABRA_RESERVADA_PARA = r'para'
t_PALABRA_RESERVADA_RURAY = r'ruray'
t_PALABRA_RESERVADA_KUTIPAY = r'kutipay'
t_PALABRA_RESERVADA_IMPRIMIY = r'imprimiy'
t_PALABRA_RESERVADA_AYLLU = r'ayllu'
t_PALABRA_RESERVADA_VAR = r'variable'
t_PALABRA_RESERVADA_TAKYAQ = r'takyaq'

def t_YUPAY_TOKEN(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

def t_CHIQAP_TOKEN(t):
    r'chiqap|mana_chiqap'
    t.value = True if t.value == 'chiqap' else False
    return t

def t_QILLQA_TOKEN(t):
    r'\'[^\']*\'|\"[^\"]*\"' # Single or double quoted strings
    t.value = t.value[1:-1] # Remove quotes
    return t

def t_CHIQAQP_TOKEN(t):
    r'chiqaqp' # Assuming 'chiqaqp' represents truthiness in code, adjust if needed.
    return t

def t_IDENTIFICADOR_TOKEN(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    # Check for reserved words to avoid misclassification as identifier if needed,
    # but based on the table, keywords are already defined as tokens.
    return t

def t_COMENTARIO_TOKEN_LINEA(t):
    r'\#.*'
    # No return value. Token is discarded
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \t'

# Regla para manejar caracteres ilegales
def t_error(t):
    print(f"Error léxico: Carácter ilegal '{t.value[0]}' en línea {t.lineno}, posición {t.lexpos}")
    t.lexer.skip(1)

lexer = lex.lex()

# Test it out
def test_lexer(data):
    lexer.lineno = 1  # Reset line number for each test
    lexer.input(data)
    tokens_list = []
    while True:
        tok = lexer.token()
        if not tok:
            break  # No more input
        tokens_list.append(tok)
        print(tok)  # Imprimir para visualización inmediata
    return tokens_list

# Función para leer archivo y analizar tokens
def analyze_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = file.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{filepath}'.")
        return []

    lexer.lineno = 1  # Reset line number for each analysis
    lexer.input(data)
    tokens_list = []

    while True:
        tok = lexer.token()
        if not tok:
            break  # No more input
        tokens_list.append({
            'type': tok.type,
            'value': tok.value,
            'line': tok.lineno,
            'position': tok.lexpos
        })

    return tokens_list

if __name__ == '__main__':
    # Archivos de ejemplo
    example_files = [
        "D:\\uSalle\\Software\\ejemplito1.txt",
        "D:\\uSalle\\Software\\ejemplito2.txt",
        "D:\\uSalle\\Software\\ejemplito3.txt"
   ]

    for filename in example_files:
        print(f"\n--- Analizando léxicamente {filename} ---")
        tokens = analyze_file(filename)
        for token in tokens:
            print(token)