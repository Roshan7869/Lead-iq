"use client";

import { useEffect, useState, useCallback, useRef } from 'react';
import { toast } from 'sonner';

interface SSEEvent {
  event: string;
  data: any;
}

interface UseLiveFeedOptions {
  channels?: string[];
  source?: string;
  enabled?: boolean;
}

/** 
 * SSE Live Feed hook — connects to /api/stream for real-time lead events.
 * 
 * Usage:
 *   const { events, isConnected, reconnect } = useLiveFeed({ channels: ['lead:collected'] });
 *   events.forEach(e => console.log(e.data));
 */
export function useLiveFeed(options: UseLiveFeedOptions = {}) {
  const { channels, source, enabled = true } = options;
  const [events, setEvents] = useState<SSEEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const buildUrl = useCallback(() => {
    const params = new URLSearchParams();
    if (channels && channels.length > 0) params.set('channels', channels.join(','));
    if (source) params.set('source', source);
    const query = params.toString();
    return `/api/stream${query ? '?' + query : ''}`;
  }, [channels, source]);

  const connect = useCallback(() => {
    if (!enabled) return;
    if (eventSourceRef.current) eventSourceRef.current.close();

    const url = buildUrl();
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.addEventListener('connected', (e) => {
      const data = JSON.parse(e.data);
      setIsConnected(true);
      toast.success('Live feed connected', { description: `Subscribed to ${data.channels?.length || 0} channels` });
    });

    es.addEventListener('error', (e) => {
      const data = JSON.parse((e as any).data || '{}');
      if (data.error) {
        toast.error(`Live feed error: ${data.error}`);
      }
    });

    ['lead:collected', 'lead:analyzed', 'lead:scored', 'lead:outreach', 'lead:crm_update'].forEach(channel => {
      es.addEventListener(channel, (e) => {
        try {
          const data = JSON.parse(e.data);
          setEvents(prev => [...prev.slice(-50), { event: channel, data }]); // keep last 50
        } catch {
          // ignore malformed events
        }
      });
    });

    es.addEventListener('error', () => {
      setIsConnected(false);
      // Auto-reconnect with backoff
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = setTimeout(() => {
        connect();
      }, 3000);
    });

    es.onopen = () => {
      setIsConnected(true);
    };

    es.onerror = () => {
      setIsConnected(false);
    };
  }, [buildUrl, enabled]);

  useEffect(() => {
    connect();
    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close();
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    };
  }, [connect]);

  return { events, isConnected, reconnect: connect };
}
