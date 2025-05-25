import * as THREE from 'three';
//import arbolText from '../../../arbol.txt?raw';
import arbolText from 'E:\\Compiladores\\Salida Graphviz\\arbol_parseo.txt?raw';

import { OrbitControls } from 'three/addons/controls/OrbitControls.js';


// Crear escena obvio

const scene = new THREE.Scene();
scene.background = new THREE.Color('#F0F0F0'); // color de fondo

// crear camarita, primer argumento es el angulo de vision, segundo es la relacion de aspecto, tercer argumento es el plano cercano y cuarto el plano lejano
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.z = 15;
camera.position.y = -2;


const light = new THREE.DirectionalLight(0xffffff, 10);
light.position.set(1, 1, 1);
scene.add(light);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);

document.body.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.enableZoom = true;
controls.enablePan = true;
controls.panSpeed = 1.0;
controls.maxPolarAngle = Math.PI;


function parseDot(dotText) {
  const nodeRegex = /node(\d+)\s*\[label="([^"]+)"\]/g;
  const edgeRegex = /node(\d+)\s*->\s*node(\d+)/g;
  const nodes = {};
  let match;

  // Parsear nodos
  while ((match = nodeRegex.exec(dotText)) !== null) {
      nodes[match[1]] = { id: match[1], label: match[2], children: [] };
  }

  // Parsear aristas
  while ((match = edgeRegex.exec(dotText)) !== null) {
      const parent = match[1];
      const child = match[2];
      if (nodes[parent] && nodes[child]) {
          nodes[parent].children.push(nodes[child]);
          nodes[child].parent = nodes[parent];
      }
  }

  const root = Object.values(nodes).find(n => !n.parent);
  return root;
}

function drawTree(node, x, y, z, parentMesh, level = 0, siblingIndex = 0, siblingCount = 1) {

    // Crear esfera para el nodo
    const sphereGeometry = new THREE.SphereGeometry(0.22, 16, 16);

    let nodeColor;
    if (node.label.match(/^[A-Z]$/)) { // Si es un no-terminal (una letra mayúscula)
        nodeColor = 0x3399ff; // Azul
    } else if (node.label === "epsilon") {
        nodeColor = 0xff9933; // Naranja para epsilon
    } else {
        nodeColor = 0x66cc66; // Verde para terminales
    }

    const sphereMaterial = new THREE.MeshLambertMaterial({ color: nodeColor });
    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
    sphere.position.set(x, y, z);
    scene.add(sphere);

    // Texto del nodo
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#f0f0f0'; // Fondo claro para el canvas
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    ctx.font = 'bold 24px Arial';
    ctx.fillStyle = '#000000'; // Texto negro
    ctx.textAlign = 'center';
    ctx.fillText(node.label, canvas.width/2, 35);
    
    const texture = new THREE.CanvasTexture(canvas);
    const spriteMaterial = new THREE.SpriteMaterial({ map: texture });
    const sprite = new THREE.Sprite(spriteMaterial);
    sprite.scale.set(1.2, 0.5, 1);
    sprite.position.set(x, y + 0.5, z);
    scene.add(sprite);

    // Dibujar rama al padre
    if (parentMesh) {
        const direction = new THREE.Vector3().subVectors(sphere.position, parentMesh.position);
        const length = direction.length();
        const cylinderGeometry = new THREE.CylinderGeometry(0.05, 0.05, length, 8);
        const cylinderMaterial = new THREE.MeshLambertMaterial({ color: 0x885522 });
        const cylinder = new THREE.Mesh(cylinderGeometry, cylinderMaterial);

        // Posicionar cilindro entre padre e hijo
        cylinder.position.copy(parentMesh.position).add(direction.multiplyScalar(0.5));
        cylinder.lookAt(sphere.position);
        cylinder.rotateX(Math.PI / 2);
        scene.add(cylinder);
    }
    const baseSpread = 5.0;
    
    const childSpreadFactor = Math.max(1.5, node.children.length / 1.5);
    const spread = baseSpread * childSpreadFactor / Math.sqrt(level + 1);
    
    if (node.children.length > 0) {
        const totalWidth = spread * (node.children.length - 1);
        const startX = x - totalWidth / 2;
        
        node.children.forEach((child, i) => {
            const childX = startX + i * spread;
            const childY = y - 3.0; 
            drawTree(child, childX, childY, z, sphere, level + 1, i, node.children.length);
        });
    }
}

const root = parseDot(arbolText);
drawTree(root, 0, 3, 0, null);

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

animate();

const upButton = document.createElement('button');
upButton.textContent = '↑';
upButton.style.position = 'absolute';
upButton.style.bottom = '90px';
upButton.style.right = '60px';
upButton.style.zIndex = '1000';
upButton.onclick = () => {
    camera.position.y += 5;
    controls.target.y += 5;
    controls.update();
};
document.body.appendChild(upButton);

const downButton = document.createElement('button');
downButton.textContent = '↓';
downButton.style.position = 'absolute';
downButton.style.bottom = '60px';
downButton.style.right = '60px';
downButton.style.zIndex = '1000';
downButton.onclick = () => {
    camera.position.y -= 5;
    controls.target.y -= 5;
    controls.update();
};
document.body.appendChild(downButton);

const leftButton = document.createElement('button');
leftButton.textContent = '←';
leftButton.style.position = 'absolute';
leftButton.style.bottom = '60px';
leftButton.style.right = '95px';
leftButton.style.zIndex = '1000';
leftButton.onclick = () => {
    camera.position.x -= 5;
    controls.target.x -= 5;
    controls.update();
};
document.body.appendChild(leftButton);

const rightButton = document.createElement('button');
rightButton.textContent = '→';
rightButton.style.position = 'absolute';
rightButton.style.bottom = '60px';
rightButton.style.right = '20px';
rightButton.style.zIndex = '1000';
rightButton.onclick = () => {
    camera.position.x += 5;
    controls.target.x += 5;
    controls.update();
};
document.body.appendChild(rightButton);

const controlPanel = document.createElement('div');
controlPanel.style.position = 'absolute';
controlPanel.style.top = '15px';
controlPanel.style.left = '10px';
controlPanel.style.backgroundColor = 'rgba(255, 255, 255, 0.7)';
controlPanel.style.padding = '10px';
controlPanel.style.borderRadius = '5px';
controlPanel.style.zIndex = '1000';
document.body.appendChild(controlPanel);

// Selector de temas de color
const themeSelect = document.createElement('select');
themeSelect.style.marginLeft = '5px';
const themes = {
    'Claro': { bg: '#F0F0F0', nonTerminal: 0x3399ff, terminal: 0x66cc66, epsilon: 0xff9933 },
    'Oscuro': { bg: '#222222', nonTerminal: 0x6699ff, terminal: 0x99ff99, epsilon: 0xffcc66 },
    'Pastel': { bg: '#e6f7ff', nonTerminal: 0x9370DB, terminal: 0x98FB98, epsilon: 0xFFDAB9 }
};

Object.keys(themes).forEach(theme => {
    const option = document.createElement('option');
    option.value = theme;
    option.text = theme;
    themeSelect.appendChild(option);
});

themeSelect.onchange = () => {
    const theme = themes[themeSelect.value];
    scene.background = new THREE.Color(theme.bg);
};
controlPanel.appendChild(document.createTextNode(' Tema: '));
controlPanel.appendChild(themeSelect);

// Botón para capturar screenshot
const screenshotButton = document.createElement('button');
screenshotButton.textContent = '📷';
screenshotButton.style.marginLeft = '5px';
screenshotButton.onclick = () => {
    renderer.render(scene, camera);
    const screenshot = renderer.domElement.toDataURL('image/png');
    const link = document.createElement('a');
    link.href = screenshot;
    link.download = 'arbol_sintactico.png';
    link.click();
};
controlPanel.appendChild(screenshotButton);


// Añadiendo a Gophy
const logoImage = document.createElement('img');
logoImage.src = '/src/gophy.jpg';
logoImage.style.position = 'absolute';
logoImage.style.top = '80px';
logoImage.style.right = '90px';
logoImage.style.width = '80px';
logoImage.style.height = 'auto';
logoImage.style.borderRadius = '5px';
logoImage.style.zIndex = '1001';
logoImage.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
document.body.appendChild(logoImage);

const appTitle = document.createElement('div');
appTitle.textContent = 'Gophy - WayraSimi';
appTitle.style.position = 'absolute';
appTitle.style.top = '30px';
appTitle.style.right = '30px';
appTitle.style.fontFamily = 'Arial, sans-serif';
appTitle.style.fontSize = '24px';
appTitle.style.fontWeight = 'bold';
appTitle.style.color = '#444';
appTitle.style.zIndex = '1001';
document.body.appendChild(appTitle);