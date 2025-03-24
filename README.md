# WayraSimi

WayraSimi es un lenguaje de programación compilado que combina la facilidad de uso y la sintaxis clara de **Python** con la eficiencia y el rendimiento de **Go**. Diseñado para ser una herramienta poderosa, WayraSimi ofrece una solución ideal para desarrollar aplicaciones de alto rendimiento, sistemas concurrentes y herramientas de línea de comandos, mientras mantiene una curva de aprendizaje accesible.

## Justificación y descripción del lenguaje

En WayraSimi, el desarrollador encuentra una plataforma que prioriza tanto la **productividad** como la **eficiencia en tiempo de ejecución**, logrando unir lo mejor de dos mundos:

- **Simplicidad y legibilidad de Python**: Para garantizar una experiencia intuitiva.
- **Robustez y rendimiento de Go**: Orientado a aplicaciones de alto rendimiento.

## Características principales

- **Sintaxis inspirada en Python**: Utiliza la indentación para definir bloques de código, maximizando la legibilidad y simplicidad.
- **Tipado estático con inferencia de tipos**: Garantiza seguridad y rendimiento, minimizando la verbosidad del código.
- **Concurrencia integrada**: Incluye soporte nativo para gorutinas y canales, facilitando el desarrollo de sistemas concurrentes.
- **Compilación a código nativo**: Produce binarios de alto rendimiento compilando directamente a código máquina.
- **Manejo de errores simplificado**: Combina la explicitud de Go con una sintaxis más sencilla y menos repetitiva.

## Implementación de Lexemas

WayraSimi utiliza el siguiente código basado en Python para definir su tabla de tokens y las expresiones regulares asociadas:

```python
import ply.lex as lex

# Tabla de lexemas para WayraSimi
tokens = [
    'YUPAY_TOKEN',  # Número o decimal
    'CHIQAP_TOKEN',  # Booleano
    'QILLQA_TOKEN',  # Texto o letra
    'IDENTIFICADOR_TOKEN',  # Identificador de variables o funciones
    'OPERADOR_MAS',  # +
    'OPERADOR_MENOS',  # -
    # Otros tokens...
]

# Expresiones regulares para tokens simples
t_OPERADOR_MAS = r'\+'
t_OPERADOR_MENOS = r'-'

def t_YUPAY_TOKEN(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

def t_CHIQAP_TOKEN(t):
    r'chiqap|mana_chiqap'
    t.value = True if t.value == 'chiqap' else False
    return t

# Manejo de errores léxicos
def t_error(t):
    print(f"Error léxico: Carácter ilegal '{t.value[0]}' en línea {t.lineno}, posición {t.lexpos}")
    t.lexer.skip(1)

lexer = lex.lex()
