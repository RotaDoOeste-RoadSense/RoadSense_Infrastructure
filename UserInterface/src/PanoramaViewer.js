import React, { useEffect, useRef } from 'react';
import * as PANOLENS from 'panolens';
import * as THREE from 'three';

const PanoramaViewer = ({ imageSrc }) => {
  const viewerRef = useRef(null);
  const viewerInstance = useRef(null); // Ref para armazenar a instância do viewer
  const panoramaRef = useRef(null);

  useEffect(() => {
    if (!viewerInstance.current) {
      const panorama = new PANOLENS.ImagePanorama(imageSrc);
      panoramaRef.current = panorama;

      viewerInstance.current = new PANOLENS.Viewer({
        container: viewerRef.current,
        autoHideInfospot: false,
        output: 'console',
      });

      viewerInstance.current.add(panorama);
    } else {
      const panorama = new PANOLENS.ImagePanorama(imageSrc);
      panoramaRef.current = panorama;
      viewerInstance.current.add(panorama);
    }

    return () => {
      if (viewerInstance.current) {
        viewerInstance.current.dispose();
      }
    };
  }, [imageSrc]);

  const createRectangle = (coords, imageWidth, imageHeight) => {
    const { x1, y1, x2, y2 } = coords;

    // Convertendo coordenadas para o espaço panorâmico
    const vertices = [
      convertCoordsToPanorama(x1, y1, imageWidth, imageHeight),
      convertCoordsToPanorama(x2, y1, imageWidth, imageHeight),
      convertCoordsToPanorama(x2, y2, imageWidth, imageHeight),
      convertCoordsToPanorama(x1, y2, imageWidth, imageHeight),
      convertCoordsToPanorama(x1, y1, imageWidth, imageHeight),
    ];

    // Criando a geometria e o material para a linha
    const geometry = new THREE.BufferGeometry().setFromPoints(vertices);
    const material = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 5 }); // Ajuste a largura da linha aqui

    // Criando a linha e adicionando ao panorama
    const line = new THREE.Line(geometry, material);

    if (panoramaRef.current) {
      panoramaRef.current.add(line);
    }
  };

  const convertCoordsToPanorama = (x, y, imageWidth, imageHeight) => {
    const phi = (x / imageWidth) * 2 * Math.PI;
    const theta = (y / imageHeight) * Math.PI;

    const radius = 3500;
    const sphericalCoords = new THREE.Vector3(
      radius * Math.sin(theta) * Math.cos(phi),
      radius * Math.cos(theta),
      radius * Math.sin(theta) * Math.sin(phi)
    );

    return sphericalCoords;
  };

  // Exemplo de como chamar createRectangle
  useEffect(() => {
    if (panoramaRef.current) {
      const coords = {
        x1: 2216 + 3072,
        y1: 986,
        x2: 2412 + 3072,
        y2: 1085
      };
      const imageWidth = 8192; // Largura da sua imagem
      const imageHeight = 2048; // Altura da sua imagem
      createRectangle(coords, imageWidth, imageHeight);
    }
  }, [imageSrc]);

  return <div ref={viewerRef} style={{ width: '100%', height: '100vh' }} />;
};

export default PanoramaViewer;
