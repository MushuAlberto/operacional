
import { GoogleGenAI, Type } from "@google/genai";
import { DataRow, DashboardConfig } from "../types";

// Always use process.env.API_KEY directly when initializing the client
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const analyzeLogisticsWithGemini = async (data: any[], date: string): Promise<DashboardConfig> => {
  const sample = data.slice(0, 10);
  const columns = ["Producto", "Destino", "Ton_Prog", "Ton_Real", "Eq_Prog", "Eq_Real"];

  const prompt = `
    Eres un experto en logística para una operación de litio. Analiza la jornada del ${date}.
    Columnas disponibles: ${columns.join(", ")}
    Muestra de datos: ${JSON.stringify(sample)}

    Tu tarea:
    1. Genera un "summary" ejecutivo (máximo 2 frases) que resuma el desempeño de la jornada.
    2. Crea 4 KPIs relevantes (label, value).
  `;

  try {
    const response = await ai.models.generateContent({
      model: "gemini-3-flash-preview",
      contents: prompt,
      config: { 
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            summary: { type: Type.STRING },
            suggestedKPIs: {
              type: Type.ARRAY,
              items: {
                type: Type.OBJECT,
                properties: {
                  label: { type: Type.STRING },
                  value: { type: Type.STRING }
                },
                required: ["label", "value"]
              }
            }
          },
          required: ["summary", "suggestedKPIs"]
        }
      }
    });

    return JSON.parse(response.text || '{}');
  } catch (error) {
    console.error("Error en Gemini:", error);
    return {
      summary: "Error al generar análisis automático.",
      suggestedKPIs: []
    };
  }
};

export const chatWithLogisticsIA = async (data: any[], query: string): Promise<string> => {
  const prompt = `
    Contexto: Reporte de Despachos de Litio.
    Datos: ${JSON.stringify(data.slice(0, 50))}
    Pregunta: ${query}
  `;
  const response = await ai.models.generateContent({
    model: "gemini-3-flash-preview",
    contents: prompt,
  });
  return response.text || "No hay respuesta.";
};
