"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

interface TypewriterProps {
  text: string | string[];
  cursorColor?: string;
  speed?: number;
  waitTime?: number;
  className?: string;
}

export function TypewriterEffect({
  text,
  cursorColor = "#22c55e",
  speed = 50,
  waitTime = 2000,
  className,
}: TypewriterProps) {
  const [displayText, setDisplayText] = useState("");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);
  const [loopNum, setLoopNum] = useState(0);

  useEffect(() => {
    const textArray = Array.isArray(text) ? text : [text];
    const currentText = textArray[loopNum % textArray.length];

    const handleTyping = () => {
      if (isDeleting) {
        setDisplayText((prev) => prev.substring(0, prev.length - 1));
      } else {
        setDisplayText((prev) => currentText.substring(0, prev.length + 1));
      }

      if (!isDeleting && displayText === currentText) {
        setTimeout(() => setIsDeleting(true), waitTime);
      } else if (isDeleting && displayText === "") {
        setIsDeleting(false);
        setLoopNum((prev) => prev + 1);
      }
    };

    const timer = setTimeout(
      handleTyping,
      isDeleting ? speed / 2 : speed
    );

    return () => clearTimeout(timer);
  }, [displayText, isDeleting, loopNum, speed, text, waitTime]);

  return (
    <span className={className}>
      {displayText}
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, repeat: Infinity, repeatType: "reverse" }}
        style={{ color: cursorColor }}
      >
        _
      </motion.span>
    </span>
  );
}

