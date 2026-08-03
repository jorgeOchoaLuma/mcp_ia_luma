// components/group-picker-card.tsx
"use client";

import { useState, useRef, useEffect } from "react";
import { z } from "zod";
import { Check, ChevronsUpDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

// 🪁 Schema real (zod) que usa useHumanInTheLoop para validar los args del agente
export const GroupPickerCardProps = z.object({
  groups: z.array(
    z.object({
      id: z.string(),
      name: z.string(),
      associated_projects: z.string().optional(),
    })
  ),
});

// Tipo TS derivado del schema, para usarlo en las props del componente
type GroupPickerCardData = z.infer<typeof GroupPickerCardProps>;

interface GroupPickerCardComponentProps extends GroupPickerCardData {
  disabled?: boolean;
  onSelect: (group: { id: string; name: string }) => void;
}

export function GroupPickerCard({
  groups = [],
  disabled,
  onSelect,
}: GroupPickerCardComponentProps) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<{ id: string; name: string } | null>(null);
  const [triggerWidth, setTriggerWidth] = useState<number>();
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (triggerRef.current) {
      setTriggerWidth(triggerRef.current.offsetWidth);
    }
  }, []);

  const handleSelect = (group: { id: string; name: string }) => {
    setSelected(group);
    setOpen(false);
    onSelect(group);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger
        render={
          <Button
            ref={triggerRef}
            variant="outline"
            role="combobox"
            aria-expanded={open}
            disabled={disabled}
            className="w-full justify-between font-normal"
          >
            {selected ? selected.name : "Seleccionar grupo de proyectos..."}
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        }
      />
      <PopoverContent
        align="start"
        sideOffset={4}
        className="p-0"
        style={{ width: triggerWidth }}
      >
        <Command>
          <CommandInput placeholder="Buscar grupo..." />
          <CommandList>
            <CommandEmpty>No se encontró ningún grupo.</CommandEmpty>
            <CommandGroup>
              {groups.map((group) => (
                <CommandItem
                  key={group.id}
                  value={group.name}
                  onSelect={() => handleSelect(group)}
                >
                  <Check
                    className={cn(
                      "mr-2 h-4 w-4",
                      selected?.id === group.id ? "opacity-100" : "opacity-0"
                    )}
                  />
                  <div className="flex flex-col">
                    <span>{group.name}</span>
                    {group.associated_projects && (
                      <span className="text-xs text-gray-400">
                        {group.associated_projects} proyecto
                        {group.associated_projects !== "1" ? "s" : ""}
                      </span>
                    )}
                  </div>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}