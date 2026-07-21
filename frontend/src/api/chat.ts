import { apiClient } from "./client";
import type { ChatInfo, ChatMessage } from "@/types";

export async function fetchChat(chatId: string): Promise<ChatInfo> {
  const { data } = await apiClient.get<ChatInfo>(`/chats/${chatId}`);
  return data;
}

export async function fetchMessages(chatId: string): Promise<ChatMessage[]> {
  const { data } = await apiClient.get<ChatMessage[]>(`/chats/${chatId}/messages`);
  return data;
}
