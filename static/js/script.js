// Manejo de tabs
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Quitar active de todos
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Activar el seleccionado
        btn.classList.add('active');
        const tabId = btn.getAttribute('data-tab');
        document.getElementById(tabId).classList.add('active');
    });
});

// Preview de imagen
document.getElementById('inputImagen').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('previewImg').src = e.target.result;
            document.getElementById('imagePreview').classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
});

// Mostrar nombre de archivo de audio
document.getElementById('inputAudio').addEventListener('change', function(e) {
    const fileName = e.target.files[0]?.name || '';
    document.getElementById('audioFileName').textContent = fileName ? `Archivo: ${fileName}` : '';
});

// Preview de imagen en multimodal
document.getElementById('inputImagenMulti').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const fileName = document.getElementById('imageMultiFileName');
        fileName.innerHTML = `<i class="fas fa-check-circle"></i> ${file.name}`;
        fileName.classList.add('active');
        
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('previewImgMulti').src = e.target.result;
            document.getElementById('imageMultiPreview').classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
});

// Mostrar nombre de archivo de audio en multimodal
document.getElementById('inputAudioMulti').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const fileName = document.getElementById('audioMultiFileName');
        fileName.innerHTML = `<i class="fas fa-check-circle"></i> ${file.name}`;
        fileName.classList.add('active');
    }
});

// Funciones auxiliares
function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

function showError(message) {
    alert('Error: ' + message);
}

// FORMULARIO DE TEXTO
document.getElementById('formTexto').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const texto = document.getElementById('inputTexto').value;
    
    if (!texto.trim()) {
        showError('Por favor escribe algún texto');
        return;
    }
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('text', texto);
        
        const response = await fetch('/api/analyze/text', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Error en el análisis');
        }
        
        mostrarResultadoTexto(data);
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
});

function mostrarResultadoTexto(data) {
    const resultado = document.getElementById('resultadoTexto');
    const sentimiento = data.sentimiento;
    
    let claseColor = 'sentimiento-neutral';
    if (sentimiento.clasificacion === 'positivo') claseColor = 'sentimiento-positivo';
    if (sentimiento.clasificacion === 'negativo') claseColor = 'sentimiento-negativo';
    
    let html = `
        <h3><i class="fas fa-chart-line"></i> Resultados del Análisis</h3>
        
        <div class="metric-cards">
            <div class="metric-card">
                <div class="label">Sentimiento</div>
                <div class="emoji">${sentimiento.emoji}</div>
                <div class="value ${claseColor}">${sentimiento.clasificacion}</div>
            </div>
            <div class="metric-card">
                <div class="label">Score</div>
                <div class="value">${sentimiento.score}</div>
                <div class="text-muted" style="font-size: 0.85rem;">Rango: -1 a +1</div>
            </div>
            <div class="metric-card">
                <div class="label">Intensidad</div>
                <div class="value">${sentimiento.intensidad}</div>
                <div class="text-muted" style="font-size: 0.85rem;">Magnitud emocional</div>
            </div>
            <div class="metric-card">
                <div class="label">Categoría</div>
                <div class="value" style="font-size: 1.3rem;">${data.categoria}</div>
            </div>
        </div>
    `;
    
    if (data.entidades && data.entidades.length > 0) {
        html += `
            <h4 style="margin-top: 20px; margin-bottom: 15px;">
                <i class="fas fa-tags"></i> Entidades Detectadas
            </h4>
            <div class="entidades-list">
        `;
        
        data.entidades.forEach(entidad => {
            html += `
                <div class="entidad-item">
                    <span class="entidad-nombre">${entidad.nombre}</span>
                    <span class="entidad-tipo">${entidad.tipo}</span>
                </div>
            `;
        });
        
        html += `</div>`;
    }
    
    html += `
        <div class="recomendacion-box">
            <h4><i class="fas fa-lightbulb"></i> Recomendación</h4>
            <p>${data.recomendacion}</p>
        </div>
    `;
    
    resultado.innerHTML = html;
    resultado.classList.remove('hidden');
    resultado.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// FORMULARIO DE AUDIO
document.getElementById('formAudio').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const audioFile = document.getElementById('inputAudio').files[0];
    
    if (!audioFile) {
        showError('Por favor selecciona un archivo de audio');
        return;
    }
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('file', audioFile);
        
        const response = await fetch('/api/analyze/audio', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Error en el análisis');
        }
        
        mostrarResultadoAudio(data);
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
});

function mostrarResultadoAudio(data) {
    const resultado = document.getElementById('resultadoAudio');
    
    let claseColor = 'sentimiento-neutral';
    if (data.sentimiento.clasificacion === 'positivo') claseColor = 'sentimiento-positivo';
    if (data.sentimiento.clasificacion === 'negativo') claseColor = 'sentimiento-negativo';
    
    let html = `
        <h3><i class="fas fa-check-circle"></i> Análisis Completado</h3>
        
        <div class="alert alert-info" style="margin-bottom: 20px;">
            <i class="fas fa-quote-left"></i>
            <div>
                <strong>Transcripción:</strong><br>
                "${data.transcripcion}"
            </div>
        </div>
        
        <div class="metric-cards">
            <div class="metric-card">
                <div class="label">Confianza Audio</div>
                <div class="value">${(data.confianza_audio * 100).toFixed(0)}%</div>
            </div>
            <div class="metric-card">
                <div class="label">Sentimiento</div>
                <div class="value ${claseColor}">${data.sentimiento.clasificacion}</div>
            </div>
            <div class="metric-card">
                <div class="label">Score</div>
                <div class="value">${data.sentimiento.score}</div>
            </div>
        </div>
    `;
    
    resultado.innerHTML = html;
    resultado.classList.remove('hidden');
    resultado.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// FORMULARIO DE IMAGEN
document.getElementById('formImagen').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const imageFile = document.getElementById('inputImagen').files[0];
    
    if (!imageFile) {
        showError('Por favor selecciona una imagen');
        return;
    }
    
    showLoading();
    
    try {
        const formData = new FormData();
        formData.append('file', imageFile);
        
        const response = await fetch('/api/analyze/image', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Error en el análisis');
        }
        
        mostrarResultadoImagen(data);
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
});

function mostrarResultadoImagen(data) {
    const resultado = document.getElementById('resultadoImagen');
    
    let html = `
        <h3><i class="fas fa-images"></i> Análisis de Imagen Completado</h3>
        
        <div class="metric-cards">
            <div class="metric-card">
                <div class="label">Rostros Detectados</div>
                <div class="value">${data.caras.cantidad}</div>
            </div>
            <div class="metric-card">
                <div class="label">Objetos Encontrados</div>
                <div class="value">${data.objetos.length}</div>
            </div>
            <div class="metric-card">
                <div class="label">Sentimiento Visual</div>
                <div class="value sentimiento-${data.sentimiento_visual}">
                    ${data.sentimiento_visual}
                </div>
            </div>
        </div>
    `;
    
    if (data.caras.cantidad > 0 && data.caras.detalles.length > 0) {
        html += `
            <h4 style="margin-top: 25px; margin-bottom: 15px;">
                <i class="fas fa-smile"></i> Emociones Detectadas
            </h4>
        `;
        
        data.caras.detalles.forEach((cara, idx) => {
            html += `
                <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <strong>Rostro ${idx + 1}:</strong> Emoción principal - 
                    <span style="color: var(--primary); font-weight: bold;">
                        ${cara.emocion_principal}
                    </span>
                    <div style="margin-top: 10px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
            `;
            
            for (let [emocion, valor] of Object.entries(cara.emociones)) {
                const porcentaje = (valor * 100).toFixed(0);
                html += `
                    <div style="font-size: 0.9rem;">
                        ${emocion}: <strong>${porcentaje}%</strong>
                        <div style="background: #e5e7eb; height: 6px; border-radius: 3px; margin-top: 3px;">
                            <div style="background: var(--primary); height: 100%; width: ${porcentaje}%; border-radius: 3px;"></div>
                        </div>
                    </div>
                `;
            }
            
            html += `
                    </div>
                </div>
            `;
        });
    }
    
    if (data.objetos.length > 0) {
        html += `
            <h4 style="margin-top: 25px; margin-bottom: 15px;">
                <i class="fas fa-cubes"></i> Objetos Identificados
            </h4>
            <div class="objetos-grid">
        `;
        
        data.objetos.slice(0, 10).forEach(obj => {
            html += `
                <span class="objeto-tag">
                    ${obj.nombre} (${(obj.confianza * 100).toFixed(0)}%)
                </span>
            `;
        });
        
        html += `</div>`;
    }
    
    if (data.texto) {
        html += `
            <div class="alert alert-info" style="margin-top: 20px;">
                <i class="fas fa-font"></i>
                <div>
                    <strong>Texto detectado en la imagen:</strong><br>
                    ${data.texto}
                </div>
            </div>
        `;
    }
    
    resultado.innerHTML = html;
    resultado.classList.remove('hidden');
    resultado.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// FORMULARIO MULTIMODAL
document.getElementById('formMultimodal').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const texto = document.getElementById('inputTextoMulti').value;
    const audioFile = document.getElementById('inputAudioMulti').files[0];
    const imageFile = document.getElementById('inputImagenMulti').files[0];
    
    if (!texto.trim() && !audioFile && !imageFile) {
        showError('Debes proporcionar al menos texto, audio o imagen');
        return;
    }
    
    showLoading();
    
    try {
        const formData = new FormData();
        
        if (texto.trim()) {
            formData.append('text', texto);
        }
        if (audioFile) {
            formData.append('audio_file', audioFile);
        }
        if (imageFile) {
            formData.append('image_file', imageFile);
        }
        
        const response = await fetch('/api/analyze/multimodal', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Error en el análisis');
        }
        
        mostrarResultadoMultimodal(data);
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
});

function mostrarResultadoMultimodal(data) {
    const resultado = document.getElementById('resultadoMultimodal');
    
    let html = `
        <h3><i class="fas fa-trophy"></i> Análisis Multimodal Completo</h3>
        
        <div class="alert alert-info">
            <i class="fas fa-info-circle"></i>
            <div>
                <strong>APIs utilizadas:</strong> ${data.apis_usadas.join(', ')}<br>
                <strong>Canales analizados:</strong> ${data.resultado_final?.canales_analizados || 'N/A'}
            </div>
        </div>
    `;
    
    if (data.resultado_final) {
        const rf = data.resultado_final;
        let claseColor = 'sentimiento-neutral';
        if (rf.sentimiento === 'positivo') claseColor = 'sentimiento-positivo';
        if (rf.sentimiento === 'negativo') claseColor = 'sentimiento-negativo';
        
        html += `
            <div style="background: linear-gradient(135deg, var(--primary), var(--secondary)); color: white; padding: 25px; border-radius: 10px; margin: 20px 0;">
                <h4 style="margin-bottom: 15px; color: white;">
                    <i class="fas fa-star"></i> Resultado Consolidado
                </h4>
                <div style="font-size: 1.8rem; font-weight: bold; margin-bottom: 10px;">
                    Sentimiento: ${rf.sentimiento.toUpperCase()}
                </div>
                <div style="font-size: 1.2rem;">
                    Score promedio: ${rf.score_promedio}
                </div>
                <hr style="margin: 15px 0; border-color: rgba(255,255,255,0.3);">
                <p style="font-size: 1.1rem; margin: 0;">
                    <i class="fas fa-lightbulb"></i> ${rf.recomendacion}
                </p>
            </div>
        `;
    }
    
    if (data.analisis_texto) {
        html += `
            <div style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 4px solid var(--info);">
                <h4><i class="fas fa-file-alt"></i> Análisis de Texto</h4>
                <p><strong>Sentimiento:</strong> ${data.analisis_texto.sentimiento.clasificacion} 
                   (Score: ${data.analisis_texto.sentimiento.score})</p>
                <p><strong>Categoría:</strong> ${data.analisis_texto.categoria}</p>
            </div>
        `;
    }
    
    if (data.analisis_audio) {
        html += `
            <div style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 4px solid var(--success);">
                <h4><i class="fas fa-microphone"></i> Análisis de Audio</h4>
                <p><strong>Transcripción:</strong> "${data.analisis_audio.transcripcion}"</p>
                <p><strong>Sentimiento:</strong> ${data.analisis_audio.sentimiento.clasificacion}</p>
            </div>
        `;
    }
    
    if (data.analisis_imagen) {
        html += `
            <div style="background: white; padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 4px solid var(--warning);">
                <h4><i class="fas fa-image"></i> Análisis de Imagen</h4>
                <p><strong>Rostros detectados:</strong> ${data.analisis_imagen.caras.cantidad}</p>
                <p><strong>Sentimiento visual:</strong> ${data.analisis_imagen.sentimiento_visual}</p>
            </div>
        `;
    }
    
    resultado.innerHTML = html;
    resultado.classList.remove('hidden');
    resultado.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}