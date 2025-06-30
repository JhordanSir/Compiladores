# WayraSimi - Compilador en Quechua

WayraSimi es un lenguaje de programación compilado que combina la facilidad de uso y la sintaxis clara de **Python** con la eficiencia y el rendimiento de **Go**. Este proyecto representa un compilador completo implementado en **Quechua**, diseñado para ser una herramienta poderosa que ofrece una solución ideal para desarrollar aplicaciones de alto rendimiento, sistemas concurrentes y herramientas de línea de comandos, mientras mantiene una curva de aprendizaje accesible.

## Autores del Proyecto

- **Jhordan Steven Octavio Huamani Huamani**
- **Miguel Angel Flores Leon**
- **Jorge Luis Ortiz Castañeda**

## Descripción del Proyecto

Este proyecto implementa un **compilador completo para el lenguaje WayraSimi**, desarrollado íntegramente en **Quechua**. El compilador está compuesto por cuatro etapas principales que procesan el código fuente hasta generar código assembly ejecutable:

1. **Analizador Léxico**: Tokeniza el código fuente
2. **Analizador Sintáctico**: Construye el árbol de sintaxis abstracta
3. **Analizador Semántico**: Verifica la semántica del programa
4. **Generador de Código Assembly**: Produce el código assembly final

El proyecto también incluye un visualizador 3D desarrollado con Three.js para mostrar el árbol sintáctico de manera interactiva.

## Justificación y Características del Lenguaje

En WayraSimi, el desarrollador encuentra una plataforma que prioriza tanto la **productividad** como la **eficiencia en tiempo de ejecución**, logrando unir lo mejor de dos mundos:

- **Simplicidad y legibilidad de Python**: Para garantizar una experiencia intuitiva.
- **Robustez y rendimiento de Go**: Orientado a aplicaciones de alto rendimiento.

### Características Principales del Lenguaje

- **Sintaxis inspirada en Python**: Utiliza la indentación para definir bloques de código, maximizando la legibilidad y simplicidad.
- **Tipado estático con inferencia de tipos**: Garantiza seguridad y rendimiento, minimizando la verbosidad del código.
- **Concurrencia integrada**: Incluye soporte nativo para gorutinas y canales, facilitando el desarrollo de sistemas concurrentes.
- **Compilación a código nativo**: Produce binarios de alto rendimiento compilando directamente a código máquina.
- **Manejo de errores simplificado**: Combina la explicitud de Go con una sintaxis más sencilla y menos repetitiva.


- **Manejo de errores simplificado**: Combina la explicitud de Go con una sintaxis más sencilla y menos repetitiva.

## Prerequisitos

- Python 3.x o superior para ejecutar el compilador
- Node.js y npm para la visualización del frontend

## Cómo Ejecutar el Proyecto

### Paso 1: Ejecutar el Compilador Completo

Para procesar un archivo de código WayraSimi, ejecute los analizadores en el siguiente orden:

#### 1. Analizador Léxico
```bash
python Analizadores/AnalizadorLexico.py
```

#### 2. Analizador Sintáctico
```bash
python Analizadores/analizadorSintactico.py
```

#### 3. Analizador Semántico
```bash
python Analizadores/AnalizadorSemantico.py
```

#### 4. Generador de Código Assembly
```bash
python Analizadores/creadorAssembly.py
```

### Paso 2: Visualizar el Árbol Sintáctico

Para ejecutar el visualizador 3D del árbol sintáctico:

```bash
cd Frontend/WayraSimi
npm install
npm run dev
```

Esto iniciará el servidor de desarrollo donde podrá visualizar el árbol sintáctico en 3D.

## ¿Cómo Funciona el Compilador?

### Proceso de Compilación

El compilador WayraSimi procesa el código fuente a través de cuatro etapas secuenciales:

#### 1. Analizador Léxico
- Lee el código fuente del archivo de entrada
- Identifica y clasifica los tokens (palabras clave, identificadores, operadores, etc.)
- Genera una secuencia de tokens para el analizador sintáctico

#### 2. Analizador Sintáctico
- Recibe los tokens del analizador léxico
- Construye el árbol de sintaxis abstracta (AST)
- Verifica que la estructura del código cumple con la gramática del lenguaje
- Exporta el árbol en formato GraphViz para visualización

#### 3. Analizador Semántico
- Analiza el AST generado por el analizador sintáctico
- Verifica la consistencia semántica del programa
- Realiza verificación de tipos y análisis de alcance de variables
- Detecta errores semánticos como variables no declaradas o incompatibilidad de tipos

#### 4. Generador de Código Assembly
- Toma el AST verificado semánticamente
- Genera código assembly optimizado
- Produce el código ejecutable final

### Visualizador 3D del Árbol Sintáctico

El frontend desarrollado con Three.js permite:

1. Leer el árbol sintáctico generado del archivo arbol.txt
2. Evaluar el formato GraphViz  
3. Crear una representación 3D interactiva del árbol sintáctico usando:
    - Esferas azules para símbolos no terminales
    - Esferas verdes para símbolos terminales  
    - Esferas naranjas para producciones epsilon

### Controles de la Visualización 3D
La vista 3D ofrece los siguientes controles:

- **Órbita**: Clic y arrastrar para rotar la cámara alrededor del árbol
- **Zoom**: Rueda del mouse para acercarse y alejarse
- **Navegación**: Teclas de flecha para navegar por el árbol
- **Selector de temas**: Para cambiar los colores de la visualización
- **Botón de captura**: Para tomar una captura de pantalla de la vista actual

## Archivos de Entrada

El compilador puede procesar archivos con extensión `.wasi` ubicados en la carpeta `Inputs/`. Ejemplos disponibles:
- `input1.wasi` - `input8.wasi`: Diferentes casos de prueba del lenguaje WayraSimi

## Estructura del Proyecto

```
├── Analizadores/           # Componentes del compilador
│   ├── AnalizadorLexico.py      # Análisis léxico
│   ├── analizadorSintactico.py  # Análisis sintáctico  
│   ├── AnalizadorSemantico.py   # Análisis semántico
│   ├── creadorAssembly.py       # Generación de código
│   └── creadorTabla.py          # Utilidades para tablas
├── Frontend/WayraSimi/     # Visualizador 3D
├── Gramática/              # Definición de la gramática
├── Inputs/                 # Archivos de prueba
└── Salida Graphviz/        # Archivos de salida
```


