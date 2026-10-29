(function () {
  "use strict";

  const host = document.getElementById("stud-viewer");
  if (!host) return;

  const loading = document.getElementById("viewer-loading");
  const fallback = document.getElementById("viewer-fallback");
  const lengthInput = document.getElementById("length");
  const depthInput = document.getElementById("depth");
  const widthInput = document.getElementById("width");
  const k2Input = document.getElementById("k2data");
  const dimensionLength = document.getElementById("dimension-length");
  const dimensionDepth = document.getElementById("dimension-depth");
  const dimensionWidth = document.getElementById("dimension-width");

  function showFallback() {
    if (loading) loading.hidden = true;
    if (fallback) fallback.hidden = false;
  }

  if (!window.THREE) {
    showFallback();
    return;
  }

  try {
    const THREE = window.THREE;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf6f9f6);

    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 1000);
    camera.position.set(5.2, 4.2, 7.2);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.domElement.setAttribute("aria-label", "Rotate the timber stud model with your mouse or touch");
    host.appendChild(renderer.domElement);

    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.07;
    controls.minDistance = 3;
    controls.maxDistance = 22;
    controls.target.set(0, 0, 0);

    scene.add(new THREE.HemisphereLight(0xffffff, 0xc9d6cb, 1.45));
    const keyLight = new THREE.DirectionalLight(0xffffff, 1.8);
    keyLight.position.set(5, 8, 6);
    keyLight.castShadow = true;
    scene.add(keyLight);
    const fillLight = new THREE.DirectionalLight(0xdbe8df, 0.8);
    fillLight.position.set(-5, 2, -4);
    scene.add(fillLight);

    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(20, 20),
      new THREE.ShadowMaterial({ opacity: 0.12 })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -1.35;
    floor.receiveShadow = true;
    scene.add(floor);

    const grid = new THREE.GridHelper(10, 20, 0xd5e0d7, 0xe7eee8);
    grid.position.y = -1.34;
    scene.add(grid);

    const woodMaterial = new THREE.MeshStandardMaterial({
      color: 0xc18b58, roughness: 0.78, metalness: 0.0
    });
    const edgeMaterial = new THREE.LineBasicMaterial({ color: 0x8b5c35, transparent: true, opacity: 0.75 });
    const supportMaterial = new THREE.MeshStandardMaterial({ color: 0x6f9680, roughness: 0.7 });
    const darkSupportMaterial = new THREE.MeshStandardMaterial({ color: 0x4e715d, roughness: 0.75 });

    const memberGroup = new THREE.Group();
    scene.add(memberGroup);
    let memberMesh = null;
    let edgeLines = null;
    let grainGroup = null;
    let supportGroup = null;

    function clearGroup(group) {
      while (group.children.length) {
        const child = group.children.pop();
        if (child.geometry) child.geometry.dispose();
      }
    }

    function positiveValue(input, fallbackValue) {
      const value = Number(input && input.value);
      return Number.isFinite(value) && value > 0 ? value : fallbackValue;
    }

    function displayNumber(value) {
      return Number(value).toLocaleString(undefined, { maximumFractionDigits: 3 });
    }

    function updateModel() {
      const rawL = positiveValue(lengthInput, 20);
      const rawD = positiveValue(depthInput, 0.5);
      const rawW = positiveValue(widthInput, 0.5);

      if (dimensionLength) dimensionLength.textContent = lengthInput && lengthInput.value ? displayNumber(rawL) : "20";
      if (dimensionDepth) dimensionDepth.textContent = depthInput && depthInput.value ? displayNumber(rawD) : "—";
      if (dimensionWidth) dimensionWidth.textContent = widthInput && widthInput.value ? displayNumber(rawW) : "—";

      // Normalize dimensions for display only. This is a schematic model, not a structural analysis.
      const largest = Math.max(rawL, rawD, rawW, 0.001);
      const length = 3.5 * rawL / largest;
      const depth = Math.max(0.12, 1.0 * rawD / largest);
      const width = Math.max(0.12, 1.0 * rawW / largest);

      if (memberMesh) {
        memberGroup.remove(memberMesh);
        memberMesh.geometry.dispose();
      }
      if (edgeLines) {
        memberGroup.remove(edgeLines);
        edgeLines.geometry.dispose();
      }
      if (grainGroup) {
        memberGroup.remove(grainGroup);
        clearGroup(grainGroup);
      }
      if (supportGroup) {
        memberGroup.remove(supportGroup);
        clearGroup(supportGroup);
      }

      const geometry = new THREE.BoxGeometry(width, length, depth);
      memberMesh = new THREE.Mesh(geometry, woodMaterial);
      memberMesh.castShadow = true;
      memberMesh.receiveShadow = true;
      memberGroup.add(memberMesh);

      const edges = new THREE.EdgesGeometry(geometry);
      edgeLines = new THREE.LineSegments(edges, edgeMaterial);
      memberGroup.add(edgeLines);

      grainGroup = new THREE.Group();
      const grainMaterial = new THREE.LineBasicMaterial({ color: 0x986a40, transparent: true, opacity: 0.42 });
      const lineCount = 5;
      for (let i = 1; i <= lineCount; i++) {
        const z = -depth / 2 + depth * i / (lineCount + 1);
        const points = [
          new THREE.Vector3(-width * 0.34, -length * 0.48, z),
          new THREE.Vector3(-width * 0.22, -length * 0.2, z),
          new THREE.Vector3(-width * 0.28, length * 0.08, z),
          new THREE.Vector3(-width * 0.18, length * 0.32, z),
          new THREE.Vector3(-width * 0.24, length * 0.48, z)
        ];
        const lineGeometry = new THREE.BufferGeometry().setFromPoints(points);
        grainGroup.add(new THREE.Line(lineGeometry, grainMaterial));
      }
      memberGroup.add(grainGroup);

      supportGroup = new THREE.Group();
      const baseY = -length / 2 - 0.12;
      const topY = length / 2 + 0.12;
      const supportGeo = new THREE.BoxGeometry(width * 1.55, 0.1, depth * 1.55);
      const baseSupport = new THREE.Mesh(supportGeo, supportMaterial);
      baseSupport.position.y = baseY;
      baseSupport.castShadow = true;
      supportGroup.add(baseSupport);
      const topSupport = new THREE.Mesh(supportGeo.clone(), darkSupportMaterial);
      topSupport.position.y = topY;
      topSupport.castShadow = true;
      supportGroup.add(topSupport);
      memberGroup.add(supportGroup);

      // Orient the long member vertically; camera framing follows the current aspect ratio.
      const selectedK2 = k2Input ? k2Input.value : "1.74";
      controls.target.set(0, 0, 0);
      if (selectedK2 === "0.41") {
        camera.position.set(5.2, 4.5, 7.2);
      } else {
        camera.position.set(5.2, 4.2, 7.2);
      }
      fitCamera(length, width, depth);
    }

    function fitCamera(length, width, depth) {
      const maxDimension = Math.max(length, width, depth);
      camera.position.set(maxDimension * 1.55, maxDimension * 1.25, maxDimension * 2.1);
      camera.near = Math.max(0.01, maxDimension / 100);
      camera.far = maxDimension * 30;
      camera.updateProjectionMatrix();
      controls.minDistance = maxDimension * 0.75;
      controls.maxDistance = maxDimension * 8;
      controls.update();
    }

    function resize() {
      const width = host.clientWidth;
      const height = host.clientHeight;
      if (!width || !height) return;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height, false);
    }

    const resizeObserver = ("ResizeObserver" in window) ? new ResizeObserver(resize) : null;
    if (resizeObserver) resizeObserver.observe(host);
    else window.addEventListener("resize", resize);

    [lengthInput, depthInput, widthInput, k2Input].forEach(function (input) {
      if (input) {
        input.addEventListener("input", updateModel);
        input.addEventListener("change", updateModel);
      }
    });

    function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }

    resize();
    updateModel();
    if (loading) loading.hidden = true;
    animate();
  } catch (error) {
    console.error("Stud preview could not initialize:", error);
    showFallback();
  }
})();
