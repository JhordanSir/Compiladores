import ply.lex as lex
from prettytable import PrettyTable


tokens = [
    'YUPAY_TOKEN',
    'CHIQI_KAY_TOKEN',
    'QILLQA_TOKEN',
    'CHIQAP_TOKEN',
    'IDENTIFICADOR_TOKEN',
    'OPERADOR_MAS',
    'OPERADOR_MENOS',
    'OPERADOR_PACHA',
    'OPERADOR_RAKI',
    'OPERADOR_MODULO',
    'OPERADOR_ASIGNACION',
    'OPERADOR_IGUALDAD',
    'OPERADOR_MANA_IGUAL',
    'OPERADOR_MENOR',
    'OPERADOR_MAYOR',
    'OPERADOR_MENOR_IGUAL',
    'OPERADOR_MAYOR_IGUAL',
    'OPERADOR_LOGICO_WAN',
    'OPERADOR_LOGICO_UTAQ',
    'OPERADOR_LOGICO_MANA',
    'PARENTESIS_ABRE',
    'PARENTESIS_CIERRA',
    'LLAVE_ABRE',
    'LLAVE_CIERRA',
    'CORCHETE_ABRE',
    'CORCHETE_CIERRA',
    'COMA_TOKEN',
    'PUNTO_TOKEN',
    'DOS_PUNTOS_TOKEN',
    'PUNTO_Y_COMA_TOKEN',
    'COMENTARIO_TOKEN_LINEA',
    'COMENTARIO_TOKEN_BLOQUE_ABRE',
    'COMENTARIO_TOKEN_BLOQUE_CIERRA',
    'PALABRA_RESERVADA_SICHUS',
    'PALABRA_RESERVADA_MANA_SICHUS',
    'PALABRA_RESERVADA_MANA',
    'PALABRA_RESERVADA_PARA',
    'PALABRA_RESERVADA_RURAY',
    'PALABRA_RESERVADA_KUTIPAY',
    'PALABRA_RESERVADA_IMPRIMIY',
    'PALABRA_RESERVADA_AYLLU',
    'PALABRA_RESERVADA_VAR',
    'PALABRA_RESERVADA_TAKYAQ',
    'PALABRA_RESERVADA_UYWA',
    'PALABRA_RESERVADA_UYA',
    'HATUN_RURAY_TOKEN',
]

reserved_words = {
    'sichus': 'PALABRA_RESERVADA_SICHUS',
    'mana sichus': 'PALABRA_RESERVADA_MANA_SICHUS',
    'mana': 'PALABRA_RESERVADA_MANA',
    'para': 'PALABRA_RESERVADA_PARA',
    'ruray': 'PALABRA_RESERVADA_RURAY',
    'kutipay': 'PALABRA_RESERVADA_KUTIPAY',
    'imprimiy': 'PALABRA_RESERVADA_IMPRIMIY',
    'ayllu': 'PALABRA_RESERVADA_AYLLU',
    'variable': 'PALABRA_RESERVADA_VAR',
    'takyaq': 'PALABRA_RESERVADA_TAKYAQ',
    'uywa': 'PALABRA_RESERVADA_UYWA',
    'uya': 'PALABRA_RESERVADA_UYA',
    'chiqap': 'CHIQAP_TOKEN',
    'mana_chiqap': 'CHIQAP_TOKEN',
    'wan': 'OPERADOR_LOGICO_WAN',
    'utaq': 'OPERADOR_LOGICO_UTAQ'
}

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

def t_CHIQI_KAY_TOKEN(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_YUPAY_TOKEN(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_QILLQA_TOKEN(t):
    r'("([^"]*)")|(\'([^\']*)\')'
    t.value = t.value[1:-1]
    return t

def t_HATUN_RURAY_TOKEN(t):
    r'hatun_ruray'
    return t

def t_IDENTIFICADOR_TOKEN(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    if t.value in reserved_words:
        t.type = reserved_words[t.value]
    return t

def t_COMENTARIO_TOKEN_LINEA(t):
    r'\#.*'
    pass

def t_COMENTARIO_TOKEN_BLOQUE_ABRE(t):
    r'/\*'
    print(">> COMENTARIO_TOKEN_BLOQUE_ABRE encontrado")
    t.lexer.comment_start = t.lexer.lexpos
    t.lexer.level = 1
    t.lexer.begin('comment')

def t_comment_COMENTARIO_TOKEN_BLOQUE_CIERRA(t):
    r'\*/'
    print(">> COMENTARIO_TOKEN_BLOQUE_CIERRA encontrado") 
    t.lexer.level -= 1
    if t.lexer.level == 0:
        t.lexer.begin('INITIAL')

def t_comment_error(t):
    print(f">> ERROR en comentario de bloque en pos {t.lexer.comment_start}: '{t.value[0]}'")
    print(f"Estado Actual: {t.lexer.current_state()}")
    t.lexer.skip(1)

def t_comment_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_comment_ignore = r'.'


states = (
   ('comment','exclusive'),
)

t_ignore           = ' \t\r'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_ANY_error(t): 
    print(f"Carácter alterno '{t.value[0]}' en la línea {t.lineno}, posición {t.lexpos}, estado: {t.lexer.current_state()}")
    t.lexer.skip(1)

lexer = lex.lex()

def analyze_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            data = file.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{filepath}'.")
        return

    lexer.input(data)
    tokens_list = []

    table = PrettyTable(["Tipo", "Valor", "Línea", "Posición"])

    while True:
        tok = lexer.token()
        if not tok:
            break
        tokens_list.append(tok)
        table.add_row([tok.type, tok.value, tok.lineno, tok.lexpos])
    print(table)
    return tokens_list

if __name__ == '__main__':
    example_files = [
        "ejemplito1.txt",
        "ejemplito2.txt",
        "ejemplito3.txt",
        "ejemplito4.txt",
        "ejemplito5.txt"
    ]

    for filepath in example_files:
        print(f"\n--- Analizando el archivo: {filepath} ---")
        tokens = analyze_file(filepath)
        if tokens:
            print(f"Se analizaron {len(tokens)} tokens en el archivo '{filepath}'.")