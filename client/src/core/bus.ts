type EventHandler<T> = (payload: T) => void;

export class EventBus {
  private listeners: Map<string, EventHandler<any>[]> = new Map();

  emit<T>(eventName: string, payload: T): void {
    const handlers = this.listeners.get(eventName) || [];
    for (const handler of handlers) {
      try {
        handler(payload);
      } catch (error) {
        console.error(`Error in event handler for event "${eventName}" \n${error}:`, error);
      }
    }
  }

  on<T>(eventName: string, handler: EventHandler<T>): () => void {
    const handlers = this.listeners.get(eventName) ?? [];
    this.listeners.set(eventName, [...handlers, handler])
    return () => this.off(eventName, handler);
  }

  off<T>(eventName: string, handler: EventHandler<T>): void {
    const handlers = this.listeners.get(eventName) ?? [];
    this.listeners.set(eventName, handlers.filter((h) => h !== handler))
  }
}

export const bus = new EventBus();
