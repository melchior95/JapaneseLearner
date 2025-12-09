import { useRef, useCallback, useEffect } from 'react';

interface UseLongPressOptions {
  onLongPress: () => void;
  onClick?: () => void;
  threshold?: number; // milliseconds
}

export function useLongPress({
  onLongPress,
  onClick,
  threshold = 500,
}: UseLongPressOptions) {
  const isLongPress = useRef(false);
  const timeout = useRef<NodeJS.Timeout>();
  const target = useRef<EventTarget>();

  const start = useCallback(
    (event: React.MouseEvent | React.TouchEvent) => {
      isLongPress.current = false;
      target.current = event.target;

      timeout.current = setTimeout(() => {
        isLongPress.current = true;
        onLongPress();
      }, threshold);
    },
    [onLongPress, threshold]
  );

  const clear = useCallback(
    (event: React.MouseEvent | React.TouchEvent, shouldTriggerClick = true) => {
      timeout.current && clearTimeout(timeout.current);

      if (shouldTriggerClick && !isLongPress.current && onClick) {
        onClick();
      }

      isLongPress.current = false;
      target.current = undefined;
    },
    [onClick]
  );

  useEffect(() => {
    return () => {
      timeout.current && clearTimeout(timeout.current);
    };
  }, []);

  return {
    onMouseDown: start,
    onMouseUp: clear,
    onMouseLeave: (e: React.MouseEvent) => clear(e, false),
    onTouchStart: start,
    onTouchEnd: clear,
  };
}
