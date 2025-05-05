# WayraSimi

Este proyecto consiste en estos elementos:
1. Analizador sintáctico del lenguaje.
2. Visualizador de three.js en 3d para mostrar el árbol sintáctico

## Prerequisitos

- Tener python 3.x o más para el analizador
- Tener Node.js y npm para la visualización del frontend

## Correr Proyecto

1. Correr el analizador

El analizador lee el archivo tablita.csv

```python
python analizadorSintactico.py
```

Se puede cambiar la entrada en el archivo para probar con una expresión diferente. Esto genera un arbol sintáctico en formato DOT de GraphViz.

2. Ejecutar la visualización del FrontEnd

```javascript
cd Frontend/WayraSimi
npm install
npm run dev
```

Esto hará que corra el servidor de desarrollo en un puerto donde se podrá visualizar el árbol sintáctico en 3D.

## ¿Cómo Funciona?

### Analizador Sintáctico
El analizador sintáctico realiza lo siguiente:

1. Carga el archivo tabla.csv
2. Tokeniza las expresiones del input
3. Aplica las reglas y genera el árbol sintáctico
4. Exporta el árbol en formato GraphViz en otro archivo llamado arbol.txt

### Visualizador 3D
El frontend usa Three.js para:

1. Leer el arbol sintáctico generado del archivo arbol.txt
2. Evalua el formato GraphViz
3. Crea una representación 3D del árbol sintáctico haciendo uso de:
    - Esferas azules para símbolos no terminales
    - Esferas verdes para símbolos terminales
    - Esferas naranjas para producciones epsilon

### Controles
La vista 3D ofrece estos controles:

- Orbita: Clic y arrastrar para rotar la cámara
- Zoom: Para acercarse y alejarse
- Flechas: Para navegar por el árbol
- Selector de temas: Para cambiar los colores de la visualización
- Botón de Screenshot: Para capturar la vista actual del árbol
