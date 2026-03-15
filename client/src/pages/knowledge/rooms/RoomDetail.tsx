import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { RatingBadge } from '@/components/ui/rating-badge'
import { Slider } from '@/components/ui/slider'
import { SpecTag } from '@/components/ui/spec-tag'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Textarea } from '@/components/ui/textarea'
import { useCreateRoom, useDeleteRoom, useUpdateRoom, type RoomResponse } from '@/hooks/useRooms'
import { zodResolver } from '@hookform/resolvers/zod'
import { useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Loader2, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'
import { PhotoManager } from './PhotoManager'

const roomSchema = z.object({
  room_name: z.string().min(1, 'Room name is required'),
  room_type: z.string().min(1, 'Room type is required'),
  summary: z.string().min(1, 'Summary is required'),
  bed_queen: z.number().min(0),
  bed_single: z.number().min(0),
  baths: z.number().min(0),
  size: z.number().min(0),
  price_weekdays: z.number().min(0),
  price_weekends_holidays: z.number().min(0),
  price_ny_songkran: z.number().min(0),
  max_guests: z.number().min(1),
  sea_view: z.number().min(1).max(10),
  privacy: z.number().min(1).max(10),
  room_design: z.number().min(1).max(10),
  room_newness: z.number().min(1).max(10),
  steps_to_beach: z.number().min(1).max(10),
  steps_to_restaurant: z.number().min(1).max(10),
  tags: z.string().optional(),
})

type RoomFormValues = z.infer<typeof roomSchema>

interface RoomDetailProps {
  room?: RoomResponse | null
  isNew?: boolean
  tab?: string
  onTabChange?: (tab: string) => void
}

export function RoomDetail({ room, isNew = false, tab, onTabChange }: RoomDetailProps) {
  const navigate = useNavigate()
  const [localTab, setLocalTab] = useState('details')
  const activeTab = tab ?? localTab
  const setActiveTab = onTabChange ?? setLocalTab
  const [tags, setTags] = useState<string[]>(room?.tags?.split(',').map((t) => t.trim()).filter(Boolean) || [])
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const createRoom = useCreateRoom()
  const updateRoom = useUpdateRoom()
  const deleteRoom = useDeleteRoom()
  const isLoading = createRoom.isPending || updateRoom.isPending

  const form = useForm<RoomFormValues>({
    resolver: zodResolver(roomSchema),
    defaultValues: room
      ? {
          room_name: room.room_name,
          room_type: room.room_type,
          summary: room.summary,
          bed_queen: room.bed_queen,
          bed_single: room.bed_single,
          baths: room.baths,
          size: room.size,
          price_weekdays: room.price_weekdays,
          price_weekends_holidays: room.price_weekends_holidays,
          price_ny_songkran: room.price_ny_songkran,
          max_guests: room.max_guests,
          sea_view: room.sea_view,
          privacy: room.privacy,
          room_design: room.room_design,
          room_newness: room.room_newness,
          steps_to_beach: room.steps_to_beach,
          steps_to_restaurant: room.steps_to_restaurant,
          tags: room.tags || '',
        }
      : {
          room_name: '',
          room_type: '',
          summary: '',
          bed_queen: 0,
          bed_single: 0,
          baths: 1,
          size: 0,
          price_weekdays: 0,
          price_weekends_holidays: 0,
          price_ny_songkran: 0,
          max_guests: 2,
          sea_view: 5,
          privacy: 5,
          room_design: 5,
          room_newness: 5,
          steps_to_beach: 5,
          steps_to_restaurant: 5,
          tags: '',
        },
  })

  const handleTagsChange = (input: string) => {
    const tagList = input.split(',').map((t) => t.trim()).filter(Boolean)
    setTags(tagList)
  }

  const onSubmit = async (values: RoomFormValues) => {
    try {
      if (isNew) {
        const newRoom = await createRoom.mutateAsync(values)
        toast.success('Room created successfully')
        navigate({ to: `/knowledge/rooms/${newRoom.id}` })
      } else if (room) {
        await updateRoom.mutateAsync({ id: room.id, data: values })
        form.reset(values)
        toast.success('Room updated successfully')
      }
    } catch (error) {
      toast.error('Failed to save room')
    }
  }

  const handleDelete = async () => {
    if (!room) return
    try {
      await deleteRoom.mutateAsync(room.id)
      toast.success('Room deleted successfully')
      navigate({ to: '/knowledge/rooms' })
    } catch (error) {
      toast.error('Failed to delete room')
    }
  }

  return (
    <div className="flex flex-col h-screen">
      {/* Breadcrumb */}
      <div className="border-b px-8 py-4 bg-background flex items-center gap-2">
        <button
          onClick={() => navigate({ to: '/knowledge/rooms' })}
          className="cursor-pointer text-muted-foreground hover:text-foreground transition-colors p-1 rounded hover:bg-muted"
          aria-label="Back to rooms"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <span className="text-sm text-muted-foreground">Rooms</span>
        <span className="text-sm text-muted-foreground">/</span>
        <span className="text-sm font-medium">{isNew ? 'New Room' : room?.room_name || 'Loading...'}</span>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col border-t">
        {/* Tabs Header */}
        <div className="border-b bg-background">
          <div className="px-8">
            <TabsList variant="underline">
              <TabsTrigger variant="underline" value="details">Room Details</TabsTrigger>
              <TabsTrigger variant="underline" value="attributes">Attributes</TabsTrigger>
              <TabsTrigger variant="underline" value="photos" disabled={isNew}>Photos</TabsTrigger>
            </TabsList>
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-2xl mx-auto">
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="pb-24">
              {/* Details Tab */}
              <TabsContent value="details" className="space-y-10 m-0 animate-in fade-in duration-200">
                <div className="space-y-8">
                  {/* Room Name & Type */}
                  <div className="grid grid-cols-2 gap-x-6 gap-y-5">
                    <FormField
                      control={form.control}
                      name="room_name"
                      render={({ field }: any) => (
                        <FormItem>
                          <FormLabel>Room Name</FormLabel>
                          <FormControl>
                            <Input {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="room_type"
                      render={({ field }: any) => (
                        <FormItem>
                          <FormLabel>Room Type</FormLabel>
                          <FormControl>
                            <Input placeholder="e.g., Suite, Bungalow" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  {/* Tags */}
                  <FormField
                    control={form.control}
                    name="tags"
                    render={({ field }: any) => (
                      <FormItem>
                        <FormLabel>Tags (comma-separated)</FormLabel>
                        <FormControl>
                          <Input
                            placeholder="e.g., ocean view, wifi, ac"
                            {...field}
                            onChange={(e) => {
                              field.onChange(e)
                              handleTagsChange(e.target.value)
                            }}
                          />
                        </FormControl>
                        <FormMessage />
                        {tags.length > 0 && (
                          <div className="flex gap-2 flex-wrap mt-2">
                            {tags.map((tag) => (
                              <span
                                key={tag}
                                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-colors"
                                style={{
                                  backgroundColor: 'var(--tropical-sand)',
                                  color: 'oklch(0.2 0 0)',
                                }}
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </FormItem>
                    )}
                  />

                  {/* Summary */}
                  <div>
                    <FormField
                      control={form.control}
                      name="summary"
                      render={({ field }: any) => (
                        <FormItem>
                          <FormLabel>Summary</FormLabel>
                          <FormControl>
                            <Textarea placeholder="Brief overview of this room..." rows={10} {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  {/* Pricing Subsection */}
                  <div>
                    <div className="flex items-baseline gap-2 mb-4">
                      <h3 className="text-sm font-semibold">Pricing</h3>
                      <span className="text-xs text-muted-foreground font-normal">THB / night</span>
                    </div>
                    <div className="grid grid-cols-3 gap-x-6 gap-y-5">
                      <FormField
                        control={form.control}
                        name="price_weekdays"
                        render={({ field }: any) => (
                          <FormItem>
                            <FormLabel>Weekday</FormLabel>
                            <FormControl>
                              <Input type="number" min="0" step="0.01" {...field} onChange={(e) => field.onChange(Number(e.target.value))} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="price_weekends_holidays"
                        render={({ field }: any) => (
                          <FormItem>
                            <FormLabel>Weekend/Holiday</FormLabel>
                            <FormControl>
                              <Input type="number" min="0" step="0.01" {...field} onChange={(e) => field.onChange(Number(e.target.value))} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="price_ny_songkran"
                        render={({ field }: any) => (
                          <FormItem>
                            <FormLabel>NY/Songkran</FormLabel>
                            <FormControl>
                              <Input type="number" min="0" step="0.01" {...field} onChange={(e) => field.onChange(Number(e.target.value))} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  </div>

                  {/* Room Specs - Always Expanded */}
                  <div>
                    <h3 className="text-sm font-semibold mb-4">Specifications</h3>
                    <div className="space-y-4">
                      <div className="flex flex-wrap gap-2">
                        {form.watch('baths') > 0 && (
                          <SpecTag>{form.watch('baths')} Bath{form.watch('baths') !== 1 ? 's' : ''}</SpecTag>
                        )}
                        {form.watch('size') > 0 && (
                          <SpecTag>{form.watch('size')} sqm</SpecTag>
                        )}
                        {form.watch('max_guests') > 0 && (
                          <SpecTag>{form.watch('max_guests')} Guest{form.watch('max_guests') !== 1 ? 's' : ''}</SpecTag>
                        )}
                      </div>
                      <div className="grid grid-cols-2 gap-x-6 gap-y-5">
                        <FormField
                          control={form.control}
                          name="bed_queen"
                          render={({ field }: any) => (
                            <FormItem>
                              <FormLabel>Queen Beds</FormLabel>
                              <FormControl>
                                <Input type="number" min="0" {...field} onChange={(e) => field.onChange(Number(e.target.value))} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={form.control}
                          name="bed_single"
                          render={({ field }: any) => (
                            <FormItem>
                              <FormLabel>Single Beds</FormLabel>
                              <FormControl>
                                <Input type="number" min="0" {...field} onChange={(e) => field.onChange(Number(e.target.value))} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={form.control}
                          name="baths"
                          render={({ field }: any) => (
                            <FormItem>
                              <FormLabel>Bathrooms</FormLabel>
                              <FormControl>
                                <Input type="number" min="0" {...field} onChange={(e) => field.onChange(Number(e.target.value))} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={form.control}
                          name="size"
                          render={({ field }: any) => (
                            <FormItem>
                              <FormLabel>Size (sqm)</FormLabel>
                              <FormControl>
                                <Input type="number" min="0" step="0.1" {...field} onChange={(e) => field.onChange(Number(e.target.value))} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />

                        <FormField
                          control={form.control}
                          name="max_guests"
                          render={({ field }: any) => (
                            <FormItem>
                              <FormLabel>Max Guests</FormLabel>
                              <FormControl>
                                <Input type="number" min="1" {...field} onChange={(e) => field.onChange(Number(e.target.value))} />
                              </FormControl>
                              <FormMessage />
                            </FormItem>
                          )}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>

              {/* Attributes Tab */}
              <TabsContent value="attributes" className="space-y-10 m-0 animate-in fade-in duration-200">
                <div>
                  <FormDescription className="mb-6 text-sm text-foreground/70">Higher = better. The agent uses these to match rooms to guests.</FormDescription>

                  <div className="grid grid-cols-2 gap-x-6 gap-y-5">
                  {[
                    { name: 'sea_view' as const, label: 'Sea View' },
                    { name: 'privacy' as const, label: 'Privacy' },
                    { name: 'room_design' as const, label: 'Room Design' },
                    { name: 'room_newness' as const, label: 'Room Newness' },
                    { name: 'steps_to_beach' as const, label: 'Beach Proximity' },
                    { name: 'steps_to_restaurant' as const, label: 'Restaurant Proximity' },
                  ].map(({ name, label }) => (
                    <FormField
                      key={name}
                      control={form.control}
                      name={name}
                      render={({ field: fieldProps }: any) => (
                        <FormItem>
                          <div className="flex justify-between items-center">
                            <FormLabel>{label}</FormLabel>
                            <RatingBadge value={fieldProps.value} />
                          </div>
                          <FormControl>
                            <Slider
                              min={1}
                              max={10}
                              step={1}
                              value={[fieldProps.value]}
                              onValueChange={(value) => fieldProps.onChange(value[0])}
                            />
                          </FormControl>
                        </FormItem>
                      )}
                    />
                  ))}
                </div>

              </div>
              </TabsContent>

              {/* Photos Tab */}
              <TabsContent value="photos" className="space-y-10 m-0 animate-in fade-in duration-200">
                {!isNew && room && (
                  <div className="w-full">
                    <PhotoManager roomId={room.id} />
                  </div>
                )}
              </TabsContent>

              </form>
            </Form>
          </div>
        </div>
      </Tabs>

      {/* Sticky footer — hidden on Photos tab */}
      {activeTab !== 'photos' && <div className="border-t bg-background px-8 py-4 flex gap-3 justify-between items-center shadow-lg shadow-black/5">
        <div>
          {!isNew && room && (
            <button
              onClick={() => setDeleteDialogOpen(true)}
              className="cursor-pointer text-destructive hover:bg-destructive/10 px-3 py-2 rounded transition-colors flex items-center gap-2 text-sm font-medium"
            >
              <Trash2 className="h-4 w-4" />
              Delete Room
            </button>
          )}
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={() => navigate({ to: '/knowledge/rooms' })}>
            Cancel
          </Button>
          <Button
            onClick={form.handleSubmit(onSubmit)}
            disabled={isLoading || !form.formState.isDirty}
            style={{
              backgroundColor: isLoading ? 'var(--tropical-coral)' : 'var(--tropical-coral)',
              color: 'white',
            }}
            className="hover:opacity-90 transition-opacity"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </div>
      </div>}

      {/* Delete confirmation dialog */}
      {!isNew && room && (
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete room</AlertDialogTitle>
              <AlertDialogDescription>
                "{room.room_name}" will be permanently deleted.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDelete}
                className="bg-destructive text-white hover:bg-destructive/90"
              >
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </div>
  )
}
