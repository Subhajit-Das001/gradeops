import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, Float, Line, OrbitControls, ContactShadows } from '@react-three/drei';
import * as THREE from 'three';

const StructuredNetwork = () => {
  const groupRef = useRef();

  // Structured Layers: Input (3) -> Processing (5) -> Output (2)
  const layers = [3, 5, 2];
  const layerSpacing = 1.6;
  const nodeSpacing = 1.0;

  const nodes = useMemo(() => {
    const temp = [];
    layers.forEach((count, i) => {
      for (let j = 0; j < count; j++) {
        temp.push({
          id: `${i}-${j}`,
          layer: i,
          position: [
            (i - (layers.length - 1) / 2) * layerSpacing,
            (j - (count - 1) / 2) * nodeSpacing,
            0
          ],
        });
      }
    });
    return temp;
  }, []);

  const connections = useMemo(() => {
    const lines = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = 0; j < nodes.length; j++) {
        if (nodes[j].layer === nodes[i].layer + 1) {
          lines.push({ start: nodes[i].position, end: nodes[j].position });
        }
      }
    }
    return lines;
  }, [nodes]);

  return (
    <group ref={groupRef}>
      {connections.map((conn, i) => (
        <group key={i}>
          {/* Darker Slate Line for visibility */}
          <Line
            points={[conn.start, conn.end]}
            color="#475569" 
            lineWidth={1.5}
            transparent
            opacity={0.4}
          />
          <PulseLine start={conn.start} end={conn.end} />
        </group>
      ))}

      {nodes.map((node, i) => (
        <Sphere key={i} position={node.position} args={[0.09, 32, 32]}>
          <meshStandardMaterial 
            color="#1e3a8a" // Deep Navy Blue
            emissive="#1e40af" 
            emissiveIntensity={1.2} 
          />
        </Sphere>
      ))}
    </group>
  );
};

const PulseLine = ({ start, end }) => {
  const pulseRef = useRef();
  const points = useMemo(() => [new THREE.Vector3(...start), new THREE.Vector3(...end)], [start, end]);

  useFrame((state) => {
    const t = (state.clock.getElapsedTime() * 0.12) % 1; 
    pulseRef.current.position.lerpVectors(points[0], points[1], t);
  });

  return (
    <Sphere ref={pulseRef} args={[0.04, 16, 16]}>
      <meshBasicMaterial color="#3b82f6" transparent opacity={0.7} />
    </Sphere>
  );
};

export default function HeroScene() {
  return (
    <div className="canvas-wrapper">
      <Canvas camera={{ position: [0, 0, 7], fov: 35 }}>
        <ambientLight intensity={0.6} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        
        {/* Allows mouse movement: Rotation only, no zoom/pan to keep it clean */}
        <OrbitControls 
          enableZoom={false} 
          enablePan={false} 
          minPolarAngle={Math.PI / 3} 
          maxPolarAngle={Math.PI / 1.5} 
        />

        <Float speed={1.2} rotationIntensity={0.2} floatIntensity={0.3}>
          <StructuredNetwork />
        </Float>

        {/* Adds a soft shadow under the structure to ground it */}
        <ContactShadows position={[0, -2.5, 0]} opacity={0.2} scale={10} blur={2} />
      </Canvas>
    </div>
  );
}