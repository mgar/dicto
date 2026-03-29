<template>
  <component
    :is="iconComponent"
    v-if="iconComponent"
    v-bind="$attrs"
  />
</template>

<script setup>
import { computed } from "vue";
import {
  ArrowLeft,
  Book,
  BookMarked,
  BookOpen,
  Bookmark,
  Check,
  ChevronLeft,
  ChevronRight,
  ChevronsRight,
  CircleCheck,
  Clipboard,
  FileText,
  Info,
  LayoutGrid,
  Lightbulb,
  List,
  Lock,
  LogOut,
  MessageSquare,
  Moon,
  Play,
  Plus,
  Send,
  Sun,
  Tag,
  X,
} from "lucide-vue-next";

defineOptions({ inheritAttrs: false });

const props = defineProps({
  name: { type: String, required: true },
});

const icons = {
  "chevron-right": ChevronRight,
  "chevron-left": ChevronLeft,
  "chevrons-right": ChevronsRight,
  "check": Check,
  "check-circle": CircleCheck,
  "x": X,
  "book": Book,
  "book-closed": BookMarked,
  "book-open": BookOpen,
  "bookmark": Bookmark,
  "chat": MessageSquare,
  "info": Info,
  "list": List,
  "file-text": FileText,
  "send": Send,
  "lightbulb": Lightbulb,
  "lock": Lock,
  "tag": Tag,
  "clipboard": Clipboard,
  "arrow-left": ArrowLeft,
  "logout": LogOut,
  "grid": LayoutGrid,
  "sun": Sun,
  "moon": Moon,
  "plus": Plus,
  "play": Play,
};

const iconComponent = computed(() => icons[props.name] ?? null);
</script>
