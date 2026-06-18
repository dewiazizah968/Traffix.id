import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "https://ayughaniyatur-traffix-backend.hf.space";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

export const unwrap = <T>(res: { data: { data: T } }): T => res.data.data;
